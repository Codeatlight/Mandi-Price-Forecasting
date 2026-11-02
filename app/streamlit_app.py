"""Mandi price forecasts: see rates, forecast ranges and spike warnings by crop and market.

Run from the project root:  streamlit run app/streamlit_app.py
"""
import base64
import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "market_data.json"
ART = Path(__file__).parent / "art"
SCENERY = ["cart", "scale", "vendor", "crate", "sack", "onion", "tomato", "potato"]
PAGE_TITLES = {"home": "The mandi is open", "forecast": "Market forecasts", "results": "How good is it?"}
CROPS = ["Onion", "Tomato", "Potato"]
HORIZONS = {"1": "1 week", "2": "2 weeks", "4": "4 weeks"}
STATUS = {"spike": ("In a spike", "bad"), "watch": ("On watch", "warn"), "normal": ("Normal", "good"),
          "unrated": ("Not rated", "plain")}
UNITS = {"per kg": ("kg", 100), "per quintal": ("quintal", 1)}
REPOSITORY = "https://github.com/Codeatlight/Mandi-Price-Forecasting"
STARTING_MARKET = "Lasalgaon"
TICKER_MARKETS_PER_CROP = 6
RESULTS = [("Tomato", "31.2%", "27.1%", "13.1%", "83.5%", "85% warned, 17% of alerts correct"),
           ("Onion", "21.4%", "19.9%", "7.0%", "78.2%", "79% warned, 46% of alerts correct"),
           ("Potato", "14.1%", "13.0%", "8.0%", "77.2%", "Only one spike, can't be judged")]
USES = [("Farmers", "Decide when to sell, or how long to store, instead of selling at the bottom of a dip."),
        ("Traders and retailers", "Plan buying and stock when a four-week price range looks likely to rise."),
        ("Food companies and caterers", "Budget ahead for ingredients that can double in weeks."),
        ("Government and analysts", "See early which markets are heating up, to time stock releases and imports.")]
STEPS = [("Read the mandi", "Daily government prices from hundreds of markets are cleaned into one weekly price."),
         ("Learn the pattern", "The model studies recent moves, seasons and what other markets are doing."),
         ("Give a range", "It shows a likely price range, and flags markets where a spike may be coming.")]

STYLE = """
<style>
.block-container {max-width: 1180px; padding-top: 3rem; padding-bottom: 3rem}
[data-testid="stHeader"] {background: transparent}
@keyframes rise {from {opacity: 0; transform: translateY(22px)} to {opacity: 1; transform: none}}
@keyframes slide {from {transform: translateX(0)} to {transform: translateX(-50%)}}
@keyframes stamp {0% {opacity: 0; transform: scale(1.6) rotate(-9deg)} 70% {transform: scale(0.96) rotate(-4deg)} 100% {opacity: 1; transform: rotate(-4deg)}}
.hero {background: #F4A81C; color: #2B1A12; border: 3px solid #2B1A12; border-radius: 6px; padding: 2.5rem;
       display: grid; grid-template-columns: 1.25fr 1fr; gap: 2.5rem; align-items: center; animation: rise 0.6s ease-out both}
.hero h1 {color: #2B1A12; font-family: "Fraunces", Georgia, serif; font-size: 4rem !important; font-weight: 900;
          letter-spacing: -0.03em; line-height: 1; margin: 0; padding: 0; animation: rise 0.7s 0.1s ease-out both}
.hero .lead {color: #2B1A12; font-size: 1.2rem; margin: 1rem 0 0; animation: rise 0.7s 0.25s ease-out both}
.stamp {display: inline-block; margin-top: 1.25rem; padding: 0.3rem 0.9rem; border: 3px solid #A63D1E; color: #A63D1E;
        font-weight: 800; font-size: 1.05rem; transform: rotate(-4deg); animation: stamp 0.5s 0.8s ease-out both}
.board {background: #22332B; color: #F7F1E3; border: 8px solid #6B4226; border-radius: 4px; padding: 1.1rem 1.25rem}
.board h2 {color: #F4A81C; font-family: "Fraunces", Georgia, serif; font-size: 1.25rem; margin: 0 0 0.6rem; padding: 0}
.rate {display: grid; grid-template-columns: 1fr auto auto; gap: 0.75rem; align-items: baseline; padding: 0.5rem 0;
       border-bottom: 1px dashed rgba(247, 241, 227, 0.35); animation: rise 0.5s ease-out both}
.rate:nth-of-type(1) {animation-delay: 0.45s} .rate:nth-of-type(2) {animation-delay: 0.65s} .rate:nth-of-type(3) {animation-delay: 0.85s}
.rate:last-of-type {border-bottom: 0}
.rate b {font-size: 1.05rem} .rate small {display: block; color: #C9D2C4; font-size: 0.8rem}
.rate strong {color: #FFFFFF; font-size: 1.5rem; font-variant-numeric: tabular-nums}
.up {color: #FF9B7A} .down {color: #8FDCA8} .flat {color: #C9D2C4}
.board p {color: #C9D2C4; font-size: 0.8rem; margin: 0.6rem 0 0}
.ticker {overflow: hidden; background: #2B1A12; color: #F7F1E3; margin: 0.75rem 0; padding: 0.55rem 0; border-radius: 4px}
.ticker div {display: inline-flex; gap: 2.5rem; white-space: nowrap; animation: slide 130s linear infinite; font-variant-numeric: tabular-nums}
.ticker:hover div {animation-play-state: paused}
.section-title {color: #2B1A12; font-family: "Fraunces", Georgia, serif; font-size: 1.9rem; font-weight: 800; margin: 1.6rem 0 0.25rem; padding: 0}
.tags {display: grid; gap: 1rem; margin: 0.75rem 0}
.tags.four {grid-template-columns: repeat(4, 1fr)} .tags.three {grid-template-columns: repeat(3, 1fr)}
.tag {background: #FFFBF2; color: #2B1A12; border: 2px solid #2B1A12; border-radius: 6px; padding: 1.1rem;
      animation: rise 0.6s ease-out both; transition: transform 0.15s}
.tag:hover {transform: translateY(-3px)}
.tag:nth-child(2) {animation-delay: 0.1s} .tag:nth-child(3) {animation-delay: 0.2s} .tag:nth-child(4) {animation-delay: 0.3s}
.tag h3 {color: #A63D1E; font-size: 1.05rem; font-weight: 800; margin: 0 0 0.35rem; padding: 0}
.tag p {color: #2B1A12; font-size: 0.95rem; margin: 0}
.tag .big {font-family: "Fraunces", Georgia, serif; font-size: 2rem; font-weight: 800; white-space: nowrap; font-variant-numeric: tabular-nums}
.tag small {color: #5E4A3D; font-size: 0.85rem}
.page-band {background: #A63D1E; color: #FFF6E6; border: 3px solid #2B1A12; border-radius: 6px; padding: 1.2rem 1.6rem; animation: rise 0.5s ease-out both}
.page-band h1 {color: #FFF6E6; font-family: "Fraunces", Georgia, serif; font-size: 2.3rem !important; font-weight: 800; margin: 0; padding: 0}
.page-band p {color: #FFE9CC; margin: 0.2rem 0 0}
.pill {display: inline-block; font-weight: 800; padding: 0.15rem 0.8rem; border: 2px solid #2B1A12; border-radius: 999px}
.pill.bad {color: #FFFFFF; background: #A63D1E} .pill.warn {color: #2B1A12; background: #F4A81C}
.pill.good {color: #FFFFFF; background: #2F5D3A} .pill.plain {color: #2B1A12; background: #E9DFC9}
.note {color: #5E4A3D; font-size: 0.9rem; margin: 0.5rem 0}
.results {width: 100%; border-collapse: collapse; font-size: 0.95rem; color: #2B1A12}
.results th {color: #5E4A3D; font-weight: 600; text-align: left; padding: 0.5rem 0.75rem 0.5rem 0; border-bottom: 2px solid #2B1A12}
.results td {padding: 0.5rem 0.75rem 0.5rem 0; border-bottom: 1px dashed #C9B999}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-secondary"] {border: 2px solid #2B1A12; border-radius: 6px; font-weight: 700}
[data-testid="stAppViewContainer"], [data-testid="stMain"] {background: transparent}
[data-testid="stMainBlockContainer"] {position: relative; z-index: 1}
.scene {position: fixed; inset: 0; z-index: -1; pointer-events: none; overflow: hidden}
.scene i {position: absolute; display: block; background-repeat: no-repeat; background-size: contain; background-position: center; opacity: 0.55}
.awning {position: absolute; top: 0; left: 0; right: 0; height: 34px;
         background: repeating-linear-gradient(90deg, #A63D1E 0 44px, #FFF3DC 44px 88px); border-bottom: 3px solid #2B1A12}
.ground {position: absolute; bottom: 0; left: 0; right: 0; height: 16px; background: #6B4226; border-top: 3px solid #2B1A12}
.scene .cart {bottom: 12px; left: 0; width: 230px; height: 115px; opacity: 0.45; animation: roll 80s linear infinite}
.scene .scale {top: 34px; left: 1.5vw; width: 150px; height: 138px; transform-origin: top center; animation: sway 7s ease-in-out infinite alternate}
.scene .vendor {bottom: 14px; right: 1.5vw; width: 130px; height: 195px}
.scene .crate {bottom: 14px; left: 2vw; width: 150px; height: 102px}
.scene .sack {bottom: 14px; right: 12vw; width: 104px; height: 116px}
.scene .onion, .scene .tomato, .scene .potato {width: 58px; height: 58px; animation: bob 6s ease-in-out infinite alternate}
.scene .onion {top: 38%; left: 1.5vw} .scene .tomato {top: 30%; right: 2vw; animation-delay: 1.2s} .scene .potato {top: 58%; right: 3vw; animation-delay: 2.4s}
@keyframes roll {from {transform: translateX(-260px)} to {transform: translateX(calc(100vw + 40px))}}
@keyframes sway {from {transform: rotate(-3deg)} to {transform: rotate(3deg)}}
@keyframes bob {from {transform: translateY(-10px) rotate(-4deg)} to {transform: translateY(10px) rotate(5deg)}}
.shutter {position: fixed; inset: 0; z-index: 9999; pointer-events: none; display: grid; place-items: center;
          background: repeating-linear-gradient(0deg, #A63D1E 0 22px, #8A3218 22px 26px); border-bottom: 10px solid #2B1A12;
          animation: shutter 0.75s 0.45s cubic-bezier(.7, 0, .3, 1) both}
.shutter span {color: #FFF3DC; font-family: "Fraunces", Georgia, serif; font-size: clamp(2rem, 6vw, 4rem); font-weight: 900; padding: 0 1rem; text-align: center}
@keyframes shutter {from {transform: translateY(0)} to {transform: translateY(-105%)}}
[class*="st-key-page-"] {animation: pagein 0.55s 0.6s ease-out both}
@keyframes pagein {from {opacity: 0; transform: translateY(26px)} to {opacity: 1; transform: none}}
@media (max-width: 1700px) {.scene .sack {display: none}}
@media (max-width: 1320px) {.scene .scale, .scene .onion, .scene .tomato, .scene .potato {opacity: 0.28}}
@media (max-width: 860px) {.scene .scale, .scene .onion, .scene .tomato, .scene .potato, .scene .sack, .scene .crate {display: none}
  .scene .vendor {opacity: 0.25}}
@media (prefers-reduced-motion: reduce) {
  .hero, .hero h1, .hero .lead, .stamp, .rate, .tag, .page-band, [class*="st-key-page-"] {animation: none}
  .ticker div, .scene i {animation: none}
  .shutter {display: none}
}
@media (max-width: 860px) {
  .hero {grid-template-columns: 1fr; padding: 1.5rem 1.25rem; gap: 1.5rem}
  .hero h1 {font-size: 2.6rem !important}
  .tags.four, .tags.three {grid-template-columns: 1fr}
  .page-band h1 {font-size: 1.8rem !important}
}
</style>
"""


@st.cache_data
def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def art_style():
    """Scenery files become CSS backgrounds, because inline SVG is removed from page text."""
    rules = []
    for name in SCENERY:
        encoded = base64.b64encode((ART / f"{name}.svg").read_bytes()).decode()
        rules.append(f".scene .{name} {{background-image: url('data:image/svg+xml;base64,{encoded}')}}")
    return "<style>" + "".join(rules) + "</style>"


def scene():
    pieces = "".join(f"<i class='{name}'></i>" for name in SCENERY)
    return f"<div class='scene' aria-hidden='true'><div class='awning'></div><div class='ground'></div>{pieces}</div>"


def shutter(page):
    """Roll the shop shutter up the first time a page opens, not on every small change."""
    if st.session_state.get("shown_page") == page:
        return
    st.session_state["shown_page"] = page
    st.html(f"<div class='shutter' aria-hidden='true'><span>{PAGE_TITLES[page]}</span></div>")


def go_to(page):
    st.session_state["page"] = page


def pretty(day):
    return date.fromisoformat(day).strftime("%d %b %Y")


def unit_choice():
    return UNITS.get(st.session_state.get("unit") or "per kg", UNITS["per kg"])


def money(value, unit):
    name, divide = unit
    return f"₹{value / divide:,.1f}" if divide > 1 else f"₹{value:,.0f}"


def latest_price(series):
    return next(v for v in reversed(series["prices"]) if v is not None)


def change_mark(series, weeks=4):
    """An arrow and percent for the change over recent reported weeks."""
    known = [v for v in series["prices"] if v is not None]
    if len(known) <= weeks:
        return "", "flat", ""
    change = known[-1] / known[-1 - weeks] - 1
    if abs(change) < 0.02:
        return "=", "flat", "steady"
    return ("▲", "up", f"{change:+.0%}") if change > 0 else ("▼", "down", f"{change:+.0%}")


def fullest(data, crop, count):
    """Live markets with the most complete recent prices."""
    live = [s for s in data["series"] if s["crop"] == crop and "forecast" in s]
    return sorted(live, key=lambda s: (s["market"] != STARTING_MARKET, sum(v is None for v in s["prices"])))[:count]


def nav(page):
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
        for key, label in [("home", "Home"), ("forecast", "Forecasts"), ("results", "How good is it?")]:
            st.button(label, key=f"nav-{key}", on_click=go_to, args=(key,), type="primary" if page == key else "secondary")
        st.segmented_control("Show prices", list(UNITS), default="per kg", key="unit", label_visibility="collapsed")


def rate_row(series, unit):
    mark, tone, text = change_mark(series)
    return (f"<div class='rate'><b>{escape(series['crop'])}<small>{escape(series['market'])}, {escape(series['state'])}</small></b>"
            f"<strong>{money(latest_price(series), unit)}</strong><span class='{tone}'>{mark} {text}</span></div>")


def ticker(data, unit):
    items = [series for crop in CROPS for series in fullest(data, crop, TICKER_MARKETS_PER_CROP)]
    parts = []
    for series in items:
        mark, tone, text = change_mark(series)
        parts.append(f"<span>{escape(series['market'])} {escape(series['crop'].lower())} <b>{money(latest_price(series), unit)}</b> "
                     f"<span class='{tone}'>{mark} {text}</span></span>")
    row = "".join(parts)
    return f"<section class='ticker' aria-label='Latest market rates'><div>{row}{row}</div></section>"


def tags(items, size):
    return f"<div class='tags {size}'>" + "".join(f"<div class='tag'><h3>{escape(t)}</h3><p>{escape(p)}</p></div>" for t, p in items) + "</div>"


def home(data, unit):
    live = [s for s in data["series"] if "forecast" in s]
    spikes = sum(1 for s in live if s["crop"] == "Onion" and s["status"] == "spike")
    onion = sum(1 for s in live if s["crop"] == "Onion")
    rows = "".join(rate_row(fullest(data, crop, 1)[0], unit) for crop in CROPS)
    st.html(f"""
    <header class="hero">
      <div>
        <h1>Where are mandi prices heading?</h1>
        <p class="lead">Early price forecasts for onion, tomato and potato across Indian wholesale markets, so nobody is caught out when prices jump.</p>
        <p class="stamp">{spikes} of {onion} onion markets in a spike</p>
      </div>
      <aside class="board">
        <h2>Rate board, ₹ per {unit[0]}</h2>{rows}
        <p>Latest prices from {pretty(data['latest_week'])}. Arrows show the last four reports.</p>
      </aside>
    </header>""")
    st.html(ticker(data, unit))
    st.button("See forecasts for your market", type="primary", on_click=go_to, args=("forecast",))
    st.html("<h2 class='section-title'>Why this matters</h2><p class='note'>Onion, tomato and potato are in almost every Indian kitchen, and their prices can double within weeks. Farmers lose out when they sell at the wrong time, and families feel it when prices jump. A few weeks' notice gives people time to plan.</p>")
    st.html("<h2 class='section-title'>Who could use it</h2>" + tags(USES, "four"))
    st.html("<h2 class='section-title'>How it works</h2>" + tags(STEPS, "three"))
    st.html(f"<p class='note'>A portfolio demo, not trading or farming advice. Prices are from Agmarknet via data.gov.in, under the Open Government License India. <a href='{REPOSITORY}' target='_blank' rel='noopener'>Code on GitHub</a></p>")


def scaled(values, unit):
    return [None if v is None else v / unit[1] for v in values]


def chart(data, series, horizon, unit):
    weeks = data["weeks"]
    prices = scaled(series["prices"], unit)
    figure = go.Figure()
    figure.add_scatter(x=weeks, y=scaled(series["normal"], unit), name="Normal level", hoverinfo="skip",
                       line={"color": "#7B8A5C", "width": 1.5, "dash": "dot"})
    figure.add_scatter(x=weeks, y=prices, name="No report", connectgaps=True, hoverinfo="skip", line={"color": "#C9B999", "width": 1.5, "dash": "dot"})
    figure.add_scatter(x=weeks, y=prices, name="Price", connectgaps=False, line={"color": "#A63D1E", "width": 2.4})
    if "forecast" in series:
        low, middle, high = scaled(series["forecast"][horizon], unit)
        end = str(date.fromisoformat(data["latest_week"]) + timedelta(weeks=int(horizon)))
        start_price = latest_price(series) / unit[1]
        figure.add_scatter(x=[data["latest_week"], end, end, data["latest_week"]], y=[start_price, high, low, start_price], fill="toself",
                           fillcolor="rgba(244,168,28,0.38)", line={"width": 0}, mode="lines", name="80% range", hoverinfo="skip")
        figure.add_scatter(x=[data["latest_week"], end], y=[start_price, middle], name="Forecast", mode="lines+markers",
                           line={"color": "#2B1A12", "width": 2.4})
    figure.update_layout(height=430, margin={"l": 10, "r": 10, "t": 30, "b": 10}, hovermode="x unified", paper_bgcolor="rgba(0,0,0,0)",
                         plot_bgcolor="rgba(0,0,0,0)", legend={"orientation": "h", "y": 1.08}, yaxis_title=f"₹ per {unit[0]}",
                         font={"color": "#2B1A12"}, transition={"duration": 400, "easing": "cubic-in-out"})
    figure.update_yaxes(gridcolor="#E6DCC4", rangemode="tozero")
    figure.update_xaxes(showgrid=False)
    st.plotly_chart(figure, width="stretch")


def forecast(data, unit):
    st.html("<div class='page-band'><h1>Market forecasts</h1><p>Pick a crop and market to see where its price may go next.</p></div>")
    crop_column, state_column, market_column, horizon_column = st.columns(4)
    crop = crop_column.selectbox("Crop", CROPS)
    series = [s for s in data["series"] if s["crop"] == crop]
    states = sorted({s["state"] for s in series})
    state = state_column.selectbox("State", states, index=states.index("Maharashtra") if "Maharashtra" in states else 0)
    in_state = sorted((s for s in series if s["state"] == state), key=lambda s: ("forecast" not in s, s["market"]))
    label = lambda s: s["market"] if "forecast" in s else f"{s['market']} (history only)"
    start = next((i for i, s in enumerate(in_state) if s["market"] == STARTING_MARKET), 0)
    chosen = market_column.selectbox("Market", in_state, index=start, format_func=label)
    horizon = horizon_column.selectbox("Forecast", list(HORIZONS), index=2, format_func=HORIZONS.get)

    if "forecast" not in chosen:
        st.warning(f"No live forecast: this market's latest price is from {pretty(chosen['last_week'])}. Agmarknet has had no Kerala data since June 2026, for example.")
    else:
        low, middle, high = chosen["forecast"][horizon]
        text, tone = STATUS[chosen["status"]]
        times = "" if chosen["vs_normal"] is None else f"{chosen['vs_normal']:.1f} times its normal level"
        st.html(f"""
        <div class="tags three">
          <div class="tag"><small>Latest price per {unit[0]}</small><p class="big">{money(latest_price(chosen), unit)}</p><small>{escape(pretty(chosen['last_week']))}</small></div>
          <div class="tag"><small>Likely in {HORIZONS[horizon]}</small><p class="big">{money(low, unit)} to {money(high, unit)}</p><small>80% range, centred near {money(middle, unit)}</small></div>
          <div class="tag"><small>Spike status</small><p style="margin: 0.5rem 0"><span class="pill {tone}">{text}</span></p><small>{times}</small></div>
        </div>""")
        if chosen["status"] == "unrated":
            st.html("<p class='note'>Potato alerts aren't shown because too few spikes occurred to test them.</p>")
        if chosen["status"] == "watch":
            st.html("<p class='note'>On watch means a spike is more likely than usual, not certain. Many alerts don't come true.</p>")
    chart(data, chosen, horizon, unit)
    st.html("<p class='note'>Dotted \"No report\" stretches are weeks when the market sent no price, such as holidays or data outages. They are not estimates. Mandi prices are wholesale, so shop prices will be higher.</p>")


def results():
    st.html("<div class='page-band'><h1>How good is it?</h1><p>Four weeks ahead, on November 2024 to October 2026, data the models never saw in development.</p></div>")
    rows = "".join(f"<tr><td>{crop}</td><td>{base}</td><td>{model}</td><td>{gain}</td><td>{held}</td><td>{alerts}</td></tr>" for crop, base, model, gain, held, alerts in RESULTS)
    st.html(f"""
    <div class="tag" style="margin-top: 0.75rem"><table class="results">
      <thead><tr><th scope="col">Crop</th><th scope="col">Next week = this week</th><th scope="col">Model error</th><th scope="col">Gain</th><th scope="col">80% range held</th><th scope="col">Spike alerts</th></tr></thead>
      <tbody>{rows}</tbody></table></div>""")
    st.markdown(
        "**Read these with care.**\n\n"
        "- Gains were smaller than in development, and the onion and potato four-week gains can't be separated from zero.\n"
        "- Four-week ranges are wide, and they hold less often during spikes.\n"
        "- Many alerts don't come true, so treat them as a reason to watch a market, not to act automatically.\n"
        "- A spike means at least twice the market's median over the previous 52 weeks.\n"
        "- These prices don't include supply or weather, so sudden shocks are hard to foresee.")


st.set_page_config(page_title="Mandi Price Forecasts", layout="wide")
st.html(STYLE)
st.html(art_style())
st.html(scene())
market_data = load()
page = st.session_state.get("page", "home")
shutter(page)
nav(page)
chosen_unit = unit_choice()
with st.container(key=f"page-{page}"):
    if page == "home":
        home(market_data, chosen_unit)
    elif page == "forecast":
        forecast(market_data, chosen_unit)
    else:
        results()
