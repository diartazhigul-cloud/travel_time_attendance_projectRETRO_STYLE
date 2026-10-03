import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from cleaning import build_tables
from i18n import PAGES, TEXTS, TRANSPORT_LABELS, describe_r

ALPHA = 0.05

st.set_page_config(
    page_title="Travel Time & Attendance",
    page_icon="📊",
    layout="wide",
)

CSS = """
<style>
.hero {
    background: linear-gradient(135deg, #0b1f3a 0%, #1d4ed8 100%);
    padding: 1.6rem 1.8rem;
    border-radius: 18px;
    color: #fff;
    margin-bottom: 1rem;
}
.hero h1 { margin: 0 0 0.4rem 0; font-size: 1.8rem; }
.hero p { margin: 0; opacity: 0.95; font-size: 1.05rem; }
.card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.8rem;
}
.big-r {
    font-size: 2.2rem;
    font-weight: 700;
    color: #1d4ed8;
    margin: 0.2rem 0;
}
.decision {
    font-size: 1.25rem;
    font-weight: 700;
    padding: 0.8rem 1rem;
    border-radius: 12px;
}
.ok { background: #ecfdf5; color: #065f46; }
.warn { background: #fff7ed; color: #9a3412; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def load_data():
    return build_tables()


def t(lang):
    return TEXTS[lang]


def transport_name(key, lang):
    return TRANSPORT_LABELS[lang].get(key, key)


def summarize(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    return {
        "mean": series.mean(),
        "median": series.median(),
        "min": series.min(),
        "max": series.max(),
        "std": series.std(ddof=1),
        "var": series.var(ddof=1),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
    }


def fisher_ci(r, n):
    if n <= 3 or abs(r) >= 1:
        return (np.nan, np.nan)
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    return float(np.tanh(z - 1.96 * se)), float(np.tanh(z + 1.96 * se))


raw_df, analysis_df = load_data()
x = analysis_df["travel_minutes"].to_numpy(dtype=float)
y = analysis_df["attendance_percent"].to_numpy(dtype=float)
n = len(analysis_df)
r, p_value = stats.pearsonr(x, y)
reg = stats.linregress(x, y)
r2 = reg.rvalue ** 2
reject = p_value < ALPHA
ci_lo, ci_hi = fisher_ci(r, n)

JUMP_TO_PAGE = {
    "overview": "home",
    "correlation": "correlation",
    "regression": "regression",
    "transport": "transport",
    "year": "year",
}

if "lang" not in st.session_state:
    st.session_state.lang = "EN"
if "page" not in st.session_state:
    st.session_state.page = "home"

st.sidebar.markdown("### 🌐")
lang = st.sidebar.radio(
    t(st.session_state.lang)["lang"],
    ["EN", "RU"],
    index=0 if st.session_state.lang == "EN" else 1,
    horizontal=True,
)
st.session_state.lang = lang
tr = t(lang)

st.sidebar.markdown("---")
st.sidebar.subheader(tr["settings"])
show_raw = st.sidebar.checkbox(tr["show_raw"], value=False)
show_clean = st.sidebar.checkbox(tr["show_clean"], value=True)

st.sidebar.markdown("---")
jump_labels = {
    "overview": tr["jump_overview"],
    "correlation": tr["jump_corr"],
    "regression": tr["jump_reg"],
    "transport": tr["jump_transport"],
    "year": tr["jump_year"],
}
jump = st.sidebar.radio(tr["analysis_jump"], list(jump_labels.keys()), format_func=lambda k: jump_labels[k])
if st.session_state.get("last_jump") != jump:
    st.session_state.page = JUMP_TO_PAGE[jump]
    st.session_state.last_jump = jump

st.sidebar.markdown("---")
page_items = PAGES[lang]
page_ids = [p[0] for p in page_items]
page_names = {p[0]: p[1] for p in page_items}
current_index = page_ids.index(st.session_state.page) if st.session_state.page in page_ids else 0
page = st.sidebar.radio(
    tr["nav"],
    page_ids,
    index=current_index,
    format_func=lambda k: page_names[k],
)
st.session_state.page = page

analysis_df = analysis_df.copy()
analysis_df["transport_label"] = analysis_df["transport_key"].map(lambda k: transport_name(k, lang))
raw_view = raw_df.copy()
raw_view["transport_label"] = raw_view["transport_key"].map(lambda k: transport_name(k, lang))


def kpi_row():
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr["metric_n"], n)
    c2.metric(tr["metric_time"], f"{analysis_df['travel_minutes'].mean():.1f} min")
    c3.metric(tr["metric_att"], f"{analysis_df['attendance_percent'].mean():.1f}%")
    c4.metric(tr["metric_r"], f"{r:.3f}")


def scatter_fig(with_line=True):
    fig = px.scatter(
        analysis_df,
        x="travel_minutes",
        y="attendance_percent",
        color="transport_label",
        hover_data=["student", "year"],
        labels={
            "travel_minutes": tr["x_axis"],
            "attendance_percent": tr["y_axis"],
            "transport_label": tr["col_transport"],
        },
        title=tr["scatter_title"],
    )
    if with_line:
        line_x = np.linspace(x.min(), x.max(), 100)
        line_y = reg.intercept + reg.slope * line_x
        fig.add_trace(
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                name="OLS",
                line=dict(color="#0f172a", width=3),
            )
        )
    fig.update_layout(legend_title_text="")
    return fig


def show_tables_if_needed():
    if show_raw:
        st.subheader(tr["raw_table"])
        st.dataframe(
            raw_view[
                [
                    "student",
                    "year",
                    "travel_raw",
                    "transport_raw",
                    "attendance_raw",
                ]
            ].rename(
                columns={
                    "student": tr["col_student"],
                    "year": tr["col_year"],
                    "travel_raw": tr["col_travel_raw"],
                    "transport_raw": tr["col_transport"],
                    "attendance_raw": tr["col_att_raw"],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
    if show_clean:
        st.subheader(tr["clean_table"])
        st.dataframe(
            analysis_df[
                [
                    "student",
                    "year",
                    "travel_minutes",
                    "transport_label",
                    "attendance_percent",
                ]
            ].rename(
                columns={
                    "student": tr["col_student"],
                    "year": tr["col_year"],
                    "travel_minutes": tr["col_travel"],
                    "transport_label": tr["col_transport"],
                    "attendance_percent": tr["col_att"],
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


# ---------- pages ----------
if page == "home":
    st.markdown(
        f"<div class='hero'><h1>📊 {tr['hero_title']}</h1><p>{tr['hero_lead']}</p></div>",
        unsafe_allow_html=True,
    )
    kpi_row()
    st.plotly_chart(scatter_fig(), use_container_width=True)
    show_tables_if_needed()

elif page == "about":
    st.header("📋 " + tr["about_title"])
    st.write(tr["about_body"])
    st.subheader(tr["methods_title"])
    st.markdown(tr["methods_list"])
    kpi_row()

elif page == "research":
    st.header("❓ " + tr["rq_title"])
    st.info(tr["rq_text"])
    st.subheader(tr["variables"])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{tr['x_title']}**")
        st.write(tr["x_text"])
    with c2:
        st.markdown(f"**{tr['y_title']}**")
        st.write(tr["y_text"])

elif page == "hypotheses":
    st.header("🎯 " + tr["obj_title"])
    st.write(tr["obj_text"])
    st.subheader(tr["hyp_title"])
    st.markdown(f"- **{tr['h0']}**")
    st.markdown(f"- **{tr['h1']}**")
    st.success(tr["alpha"])

elif page == "survey":
    st.header("📊 " + tr["survey_title"])
    st.caption(tr["survey_note"])
    st.dataframe(
        raw_view[
            ["student", "year", "travel_raw", "transport_label", "attendance_raw", "action"]
        ].rename(
            columns={
                "student": tr["col_student"],
                "year": tr["col_year"],
                "travel_raw": tr["col_travel_raw"],
                "transport_label": tr["col_transport"],
                "attendance_raw": tr["col_att_raw"],
                "action": tr["col_action"],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    show_tables_if_needed()

elif page == "cleaning":
    st.header("🧹 " + tr["clean_title"])
    st.write(tr["clean_intro"])
    st.subheader(tr["clean_examples"])
    st.markdown(
        "\n".join(
            [
                f"- {tr['ex1']}",
                f"- {tr['ex2']}",
                f"- {tr['ex3']}",
                f"- {tr['ex4']}",
                f"- {tr['ex5']}",
                f"- {tr['ex6']}",
                f"- {tr['ex7']}",
                f"- {tr['ex8']}",
            ]
        )
    )
    examples = pd.DataFrame(
        {
            tr["raw_in"]: [
                "1 сағат",
                "1.5 сағат",
                "10-15 минут",
                "20-30 минут",
                "30-50",
                "90-100%",
                "99,90%",
                "1 мин + Самолет",
            ],
            tr["cleaned_to"]: ["60 min", "90 min", "12.5 min", "25 min", "40 min", "95%", "99.9%", "excluded"],
            tr["rule"]: [
                "hours → minutes",
                "hours → minutes",
                "range midpoint",
                "range midpoint",
                "range midpoint",
                "range midpoint",
                "comma decimal",
                "unrealistic commute",
            ],
        }
    )
    st.dataframe(examples, use_container_width=True, hide_index=True)
    st.subheader(tr["excluded"])
    excluded = raw_view.loc[~raw_view["keep"]]
    st.dataframe(
        excluded[["student", "travel_raw", "transport_raw", "attendance_raw", "action"]],
        use_container_width=True,
        hide_index=True,
    )
    st.subheader(tr["kept"])
    st.dataframe(
        analysis_df[
            ["student", "travel_raw", "travel_minutes", "attendance_raw", "attendance_percent", "travel_note"]
        ],
        use_container_width=True,
        hide_index=True,
    )

elif page == "descriptive":
    st.header("📈 " + tr["desc_title"])
    kpi_row()
    time_s = summarize(analysis_df["travel_minutes"])
    att_s = summarize(analysis_df["attendance_percent"])
    table = pd.DataFrame(
        {
            "": [
                tr["mean"],
                tr["median"],
                tr["minimum"],
                tr["maximum"],
                tr["std"],
                tr["var"],
                tr["q1"],
                tr["q3"],
                tr["iqr"],
            ],
            tr["var_time"]: [
                time_s["mean"],
                time_s["median"],
                time_s["min"],
                time_s["max"],
                time_s["std"],
                time_s["var"],
                time_s["q1"],
                time_s["q3"],
                time_s["iqr"],
            ],
            tr["var_att"]: [
                att_s["mean"],
                att_s["median"],
                att_s["min"],
                att_s["max"],
                att_s["std"],
                att_s["var"],
                att_s["q1"],
                att_s["q3"],
                att_s["iqr"],
            ],
        }
    ).round(2)
    st.dataframe(table, use_container_width=True, hide_index=True)

elif page == "visualization":
    st.header("📊 " + tr["viz_title"])
    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(
            analysis_df,
            x="travel_minutes",
            nbins=10,
            title=tr["hist_time"],
            labels={"travel_minutes": tr["x_axis"]},
        )
        fig.update_layout(yaxis_title=tr["count"])
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.histogram(
            analysis_df,
            x="attendance_percent",
            nbins=10,
            title=tr["hist_att"],
            labels={"attendance_percent": tr["y_axis"]},
        )
        fig.update_layout(yaxis_title=tr["count"])
        st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(scatter_fig(), use_container_width=True)
    box = go.Figure()
    box.add_trace(go.Box(y=analysis_df["travel_minutes"], name=tr["var_time"]))
    box.add_trace(go.Box(y=analysis_df["attendance_percent"], name=tr["var_att"], yaxis="y2"))
    box.update_layout(
        title=tr["box_title"],
        yaxis=dict(title=tr["var_time"]),
        yaxis2=dict(title=tr["var_att"], overlaying="y", side="right"),
        showlegend=True,
    )
    st.plotly_chart(box, use_container_width=True)
    b1, b2 = st.columns(2)
    with b1:
        st.plotly_chart(
            px.box(analysis_df, y="travel_minutes", points="all", title=tr["var_time"], labels={"travel_minutes": tr["x_axis"]}),
            use_container_width=True,
        )
    with b2:
        st.plotly_chart(
            px.box(analysis_df, y="attendance_percent", points="all", title=tr["var_att"], labels={"attendance_percent": tr["y_axis"]}),
            use_container_width=True,
        )

elif page == "correlation":
    st.header("🔗 " + tr["corr_title"])
    phrase = describe_r(r, lang)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"<div class='card'><div>{tr['pearson']}</div><div class='big-r'>r = {r:.3f}</div><div>{phrase}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<div class='card'><div>{tr['pvalue']} = {p_value:.3f}</div><div>α = {ALPHA}</div></div>",
            unsafe_allow_html=True,
        )
    decision = tr["reject"] if reject else tr["fail"]
    klass = "ok" if reject else "warn"
    st.markdown(f"<div class='decision {klass}'>{decision}</div>", unsafe_allow_html=True)
    st.write(tr["because_lt"] if reject else tr["because_gt"])
    st.caption(f"95% CI for r (Fisher z): [{ci_lo:.3f}, {ci_hi:.3f}]")
    st.plotly_chart(scatter_fig(), use_container_width=True)

elif page == "regression":
    st.header("📉 " + tr["reg_title"])
    st.subheader(tr["equation"])
    st.latex(rf"\text{{Attendance}} = {reg.intercept:.2f} {reg.slope:+.4f} \times \text{{Travel time}}")
    c1, c2, c3 = st.columns(3)
    c1.metric(tr["slope"], f"{reg.slope:.4f}")
    c2.metric(tr["intercept"], f"{reg.intercept:.2f}")
    c3.metric(tr["r2"], f"{r2:.3f}")
    st.plotly_chart(scatter_fig(with_line=True), use_container_width=True)

elif page == "testing":
    st.header("🧪 " + tr["test_title"])
    st.markdown(f"- **{tr['test_h0']}**")
    st.markdown(f"- **{tr['test_h1']}**")
    st.write(tr["alpha"])
    c1, c2, c3 = st.columns(3)
    c1.metric("r", f"{r:.3f}")
    c2.metric(tr["pvalue"], f"{p_value:.3f}")
    c3.metric("α", str(ALPHA))
    decision = tr["reject"] if reject else tr["fail"]
    if reject:
        st.success(f"{decision}. {tr['because_lt']}")
    else:
        st.warning(f"{decision}. {tr['because_gt']}")

elif page == "year":
    st.header("👥 " + tr["year_title"])
    st.info(tr["year_note"])
    grouped = (
        analysis_df.groupby("year")
        .agg(attendance=("attendance_percent", "mean"), count=("student", "size"))
        .reset_index()
        .sort_values("year")
    )
    grouped["attendance"] = grouped["attendance"].round(1)
    st.dataframe(
        grouped.rename(columns={"year": tr["col_year"], "attendance": tr["col_att"], "count": tr["n_group"]}),
        use_container_width=True,
        hide_index=True,
    )
    fig = px.bar(
        grouped,
        x="year",
        y="attendance",
        text="attendance",
        title=tr["year_mean"],
        labels={"year": tr["col_year"], "attendance": tr["col_att"]},
    )
    fig.update_traces(texttemplate="%{text:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

elif page == "transport":
    st.header("🚌 " + tr["transport_title"])
    st.info(tr["transport_note"])
    grouped = (
        analysis_df.groupby("transport_label")
        .agg(attendance=("attendance_percent", "mean"), count=("student", "size"))
        .reset_index()
        .sort_values("attendance", ascending=False)
    )
    grouped["attendance"] = grouped["attendance"].round(1)
    st.dataframe(
        grouped.rename(
            columns={
                "transport_label": tr["col_transport"],
                "attendance": tr["col_att"],
                "count": tr["n_group"],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    fig = px.bar(
        grouped,
        x="attendance",
        y="transport_label",
        orientation="h",
        text="attendance",
        title=tr["transport_title"],
        labels={"attendance": tr["col_att"], "transport_label": tr["col_transport"]},
    )
    fig.update_traces(texttemplate="%{text:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

elif page == "bins":
    st.header("📍 " + tr["bins_title"])
    st.write(tr["bins_note"])
    order = ["0–15", "16–30", "31–60", "61+"]
    grouped = (
        analysis_df.groupby("travel_bin")
        .agg(attendance=("attendance_percent", "mean"), count=("student", "size"))
        .reindex(order)
        .dropna()
        .reset_index()
    )
    grouped["attendance"] = grouped["attendance"].round(1)
    st.dataframe(
        grouped.rename(
            columns={
                "travel_bin": tr["x_axis"],
                "attendance": tr["col_att"],
                "count": tr["n_group"],
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    fig = px.bar(
        grouped,
        x="travel_bin",
        y="attendance",
        text="attendance",
        category_orders={"travel_bin": order},
        labels={"travel_bin": tr["x_axis"], "attendance": tr["col_att"]},
    )
    fig.update_traces(texttemplate="%{text:.1f}%")
    st.plotly_chart(fig, use_container_width=True)

elif page == "interpretation":
    st.header("💡 " + tr["interp_title"])
    st.write(tr["interp_r"])
    st.markdown(f"**r = {r:.3f}** → {describe_r(r, lang)}")
    st.markdown(f"**p = {p_value:.3f}**, α = {ALPHA}")
    st.write(tr["because_lt"] if reject else tr["because_gt"])
    st.warning(tr["causation"])
    st.write(tr["interp_extra"])

elif page == "limitations":
    st.header("⚠️ " + tr["lim_title"])
    st.markdown(tr["lim_list"])
    st.info(tr["lim_cause"])
    st.markdown(
        """
```
Travel time ──► Attendance
Schedule, motivation, workload, health, transport reliability ──► Attendance
```
"""
    )

elif page == "conclusion":
    st.header("✅ " + tr["conc_title"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(tr["sample_size"], n)
    c2.metric("Pearson r", f"{r:.3f}")
    c3.metric(tr["pvalue"], f"{p_value:.3f}")
    c4.metric("α", str(ALPHA))
    decision = tr["reject"] if reject else tr["fail"]
    st.markdown(f"**{tr['result']}:** {decision}")
    st.success(tr["conc_yes"] if reject else tr["conc_no"])
    st.caption(tr["footer"])

st.sidebar.caption(f"n = {n} · r = {r:.3f} · p = {p_value:.3f}")
