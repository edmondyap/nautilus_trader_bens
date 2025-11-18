# -------------------------------------------------------------------------------------------------
#  TestSingleMakerStrategy for Nautilus Trader
#  Part of Quant Trading Platform Benchmark
# -------------------------------------------------------------------------------------------------

from collections import deque
from decimal import Decimal

from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.rust.common import LogColor
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.enums import book_type_from_str
from nautilus_trader.model.events import OrderFilled
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.model.orders import LimitOrder
from nautilus_trader.trading.strategy import Strategy


class TestSingleMakerStrategyConfig(StrategyConfig, frozen=True):
    """
    Configuration for TestSingleMakerStrategy instances.

    This strategy implements a simple market maker that maintains one bid and one ask
    order around a moving average of the mid-price, updating orders when filled or
    when the market moves beyond a tolerance threshold.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument ID for the strategy.
    spread_bps : PositiveFloat, default 10.0
        Spread around mid-price in basis points (0.1% = 10 bps).
    ma_window_minutes : PositiveInt, default 5
        Moving average window size in minutes.
    price_tolerance_bps : PositiveFloat, default 15.0
        Re-quote threshold: update if mid moves >= tolerance in basis points.
    order_size_base : Decimal, default 1.0
        Order size in base currency (e.g., 1.0 SOL).
    max_long_position : Decimal, default 5.0
        Maximum long position in base currency.
    max_short_position : Decimal, default 5.0
        Maximum short position magnitude in base currency.
    max_budget_quote : Decimal, default 5000.0
        Maximum capital in quote currency (e.g., 5000 USDT).
    book_type : str, default 'L2_MBP'
        The order book type for the strategy.

    """

    instrument_id: InstrumentId
    spread_bps: PositiveFloat = 10.0
    ma_window_minutes: PositiveInt = 5
    price_tolerance_bps: PositiveFloat = 15.0
    order_size_base: Decimal = Decimal("1.0")
    max_long_position: Decimal = Decimal("5.0")
    max_short_position: Decimal = Decimal("5.0")
    max_budget_quote: Decimal = Decimal("5000.0")
    book_type: str = "L2_MBP"


class TestSingleMakerStrategy(Strategy):
    """
    A simple market-making strategy that maintains one bid and one ask order
    around a moving average of the mid-price.

    The strategy:
    - Calculates mid-price from best bid/ask
    - Maintains a moving average of mid-prices over a time window
    - Places limit orders at MA ± spread_bps
    - Updates orders when:
      1. Orders are filled
      2. Mid-price moves more than price_tolerance_bps from last quote
    - Respects position limits and budget constraints

    Parameters
    ----------
    config : TestSingleMakerStrategyConfig
        The configuration for the instance.

    """

    def __init__(self, config: TestSingleMakerStrategyConfig) -> None:
        super().__init__(config)

        # Instrument (initialized in on_start)
        self.instrument: Instrument | None = None

        # Book type
        self.book_type: BookType = book_type_from_str(self.config.book_type)

        # State variables
        self.mid_price_history: deque = deque()  # (timestamp, mid_price) tuples
        self.current_ma_mid: float | None = None
        self.active_bid_order: LimitOrder | None = None
        self.active_ask_order: LimitOrder | None = None
        self.last_bid_quote_mid: float | None = None
        self.last_ask_quote_mid: float | None = None

        # Position tracking (Nautilus handles this, but we track for convenience)
        self.position_base: Decimal = Decimal("0.0")
        self.cash_balance_quote: Decimal = self.config.max_budget_quote

        # MA window in nanoseconds
        self.ma_window_ns = int(self.config.ma_window_minutes * 60 * 1e9)

    def on_start(self) -> None:
        """
        Actions to be performed on strategy start.
        """
        self.instrument = self.cache.instrument(self.config.instrument_id)
        if self.instrument is None:
            self.log.error(f"Could not find instrument for {self.config.instrument_id}")
            self.stop()
            return

        # Subscribe to order book deltas for market data
        self.subscribe_order_book_deltas(self.instrument.id, book_type=self.book_type)

        # Also subscribe to trade ticks for additional market signals
        self.subscribe_trade_ticks(self.instrument.id)

        self.log.info(
            f"TestSingleMakerStrategy started for {self.instrument.id} "
            f"(spread={self.config.spread_bps}bps, MA={self.config.ma_window_minutes}min, "
            f"tolerance={self.config.price_tolerance_bps}bps)",
            color=LogColor.GREEN,
        )

    def on_order_book_deltas(self, deltas: OrderBookDeltas) -> None:
        """
        Actions to be performed when order book deltas are received.

        This is the main entry point for market data updates.
        """
        self._process_market_update()

    def on_trade_tick(self, tick: TradeTick) -> None:
        """
        Actions to be performed when a trade tick is received.

        Also triggers market update processing.
        """
        self._process_market_update()

    def _process_market_update(self) -> None:
        """
        Core logic: Process market data and manage orders.

        This method:
        1. Calculates current mid-price
        2. Updates mid-price history and MA
        3. Checks if orders need to be updated
        4. Places/cancels orders as needed
        """
        if not self.instrument:
            return

        # Get current order book
        book = self.cache.order_book(self.config.instrument_id)
        if not book or not book.best_bid_price() or not book.best_ask_price():
            return

        # Calculate mid-price
        best_bid = float(book.best_bid_price())
        best_ask = float(book.best_ask_price())
        current_mid = (best_bid + best_ask) / 2.0
        current_time_ns = self.clock.timestamp_ns()

        # Update mid-price history
        self.mid_price_history.append((current_time_ns, current_mid))

        # Remove old entries outside MA window
        cutoff_time_ns = current_time_ns - self.ma_window_ns
        while self.mid_price_history and self.mid_price_history[0][0] < cutoff_time_ns:
            self.mid_price_history.popleft()

        # Calculate moving average
        if len(self.mid_price_history) > 0:
            self.current_ma_mid = sum(price for _, price in self.mid_price_history) / len(
                self.mid_price_history,
            )
        else:
            return  # Not enough data yet

        # Check if we have minimum data for MA (at least 1 minute of data)
        if len(self.mid_price_history) < 10:  # Assuming updates every few seconds
            self.log.info(
                f"Accumulating mid-price history: {len(self.mid_price_history)} samples",
                color=LogColor.BLUE,
            )
            return

        # Update position from cache
        positions = self.cache.positions_open(instrument_id=self.config.instrument_id)
        if positions:
            # Sum up all positions for this instrument
            self.position_base = sum(Decimal(str(p.quantity)) for p in positions)
        else:
            self.position_base = Decimal("0.0")

        # Check if bid order needs update
        if self.active_bid_order and (
            self.active_bid_order.is_open or self.active_bid_order.is_emulated
        ):
            if self.last_bid_quote_mid is not None:
                mid_move_bps = (
                    abs(self.current_ma_mid - self.last_bid_quote_mid)
                    / self.last_bid_quote_mid
                    * 10000
                )
                if mid_move_bps >= self.config.price_tolerance_bps:
                    self.log.info(
                        f"Canceling bid order: mid moved {mid_move_bps:.2f} bps",
                        color=LogColor.YELLOW,
                    )
                    self.cancel_order(self.active_bid_order)
                    self.active_bid_order = None
        else:
            self.active_bid_order = None  # Clear if not open

        # Check if ask order needs update
        if self.active_ask_order and (
            self.active_ask_order.is_open or self.active_ask_order.is_emulated
        ):
            if self.last_ask_quote_mid is not None:
                mid_move_bps = (
                    abs(self.current_ma_mid - self.last_ask_quote_mid)
                    / self.last_ask_quote_mid
                    * 10000
                )
                if mid_move_bps >= self.config.price_tolerance_bps:
                    self.log.info(
                        f"Canceling ask order: mid moved {mid_move_bps:.2f} bps",
                        color=LogColor.YELLOW,
                    )
                    self.cancel_order(self.active_ask_order)
                    self.active_ask_order = None
        else:
            self.active_ask_order = None  # Clear if not open

        # Place new orders if needed
        if self.active_bid_order is None:
            self._place_bid_order()

        if self.active_ask_order is None:
            self._place_ask_order()

    def _place_bid_order(self) -> None:
        """
        Place a new bid order at MA - spread_bps.

        Checks position limits and budget before placing.
        """
        if not self.instrument or self.current_ma_mid is None:
            return

        # Check position limits
        if self.position_base + self.config.order_size_base > self.config.max_long_position:
            self.log.info(
                f"Skipping bid: position limit reached ({self.position_base} + "
                f"{self.config.order_size_base} > {self.config.max_long_position})",
            )
            return

        # Calculate bid price
        bid_price_raw = self.current_ma_mid * (1 - self.config.spread_bps / 10000)
        bid_price = self.instrument.make_price(Decimal(str(bid_price_raw)))

        # Check budget
        required_cash = self.config.order_size_base * Decimal(str(bid_price))
        if self.cash_balance_quote < required_cash:
            self.log.info(
                f"Skipping bid: insufficient funds ({self.cash_balance_quote} < {required_cash})",
            )
            return

        # Create and submit order
        order = self.order_factory.limit(
            instrument_id=self.instrument.id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.config.order_size_base),
            price=bid_price,
            time_in_force=TimeInForce.GTC,
            post_only=True,
        )

        self.active_bid_order = order
        self.last_bid_quote_mid = self.current_ma_mid
        self.submit_order(order)

        self.log.info(
            f"Placed BID: {bid_price} (MA={self.current_ma_mid:.2f}, size={self.config.order_size_base})",
            color=LogColor.GREEN,
        )

    def _place_ask_order(self) -> None:
        """
        Place a new ask order at MA + spread_bps.

        Checks position limits before placing.
        """
        if not self.instrument or self.current_ma_mid is None:
            return

        # Check position limits
        if self.position_base - self.config.order_size_base < -self.config.max_short_position:
            self.log.info(
                f"Skipping ask: position limit reached ({self.position_base} - "
                f"{self.config.order_size_base} < -{self.config.max_short_position})",
            )
            return

        # Calculate ask price
        ask_price_raw = self.current_ma_mid * (1 + self.config.spread_bps / 10000)
        ask_price = self.instrument.make_price(Decimal(str(ask_price_raw)))

        # Create and submit order
        order = self.order_factory.limit(
            instrument_id=self.instrument.id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.config.order_size_base),
            price=ask_price,
            time_in_force=TimeInForce.GTC,
            post_only=True,
        )

        self.active_ask_order = order
        self.last_ask_quote_mid = self.current_ma_mid
        self.submit_order(order)

        self.log.info(
            f"Placed ASK: {ask_price} (MA={self.current_ma_mid:.2f}, size={self.config.order_size_base})",
            color=LogColor.GREEN,
        )

    def on_event(self, event) -> None:
        """
        Actions to be performed when the strategy receives an event.

        Handles order fills by updating position tracking and placing
        replacement orders.
        """
        if isinstance(event, OrderFilled):
            # Update position and cash tracking
            fill_qty = Decimal(str(event.last_qty))
            fill_price = Decimal(str(event.last_px))

            if event.order_side == OrderSide.BUY:
                self.position_base += fill_qty
                self.cash_balance_quote -= fill_qty * fill_price
                self.active_bid_order = None

                self.log.info(
                    f"BID FILLED: {fill_qty} @ {fill_price} "
                    f"(pos={self.position_base}, cash={self.cash_balance_quote:.2f})",
                    color=LogColor.CYAN,
                )

                # Place replacement bid order
                self._place_bid_order()

            elif event.order_side == OrderSide.SELL:
                self.position_base -= fill_qty
                self.cash_balance_quote += fill_qty * fill_price
                self.active_ask_order = None

                self.log.info(
                    f"ASK FILLED: {fill_qty} @ {fill_price} "
                    f"(pos={self.position_base}, cash={self.cash_balance_quote:.2f})",
                    color=LogColor.CYAN,
                )

                # Place replacement ask order
                self._place_ask_order()

    def on_stop(self) -> None:
        """
        Actions to be performed when the strategy is stopped.

        Cancels all open orders and closes positions.
        """
        if self.instrument is None:
            return

        self.log.info("Stopping strategy: canceling all orders", color=LogColor.YELLOW)
        self.cancel_all_orders(self.instrument.id)

        # Optionally close all positions on stop
        # self.close_all_positions(self.instrument.id)

    def on_reset(self) -> None:
        """
        Actions to be performed when the strategy is reset.
        """
        self.mid_price_history.clear()
        self.current_ma_mid = None
        self.active_bid_order = None
        self.active_ask_order = None
        self.last_bid_quote_mid = None
        self.last_ask_quote_mid = None
        self.position_base = Decimal("0.0")
        self.cash_balance_quote = self.config.max_budget_quote
