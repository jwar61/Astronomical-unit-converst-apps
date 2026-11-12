import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Radio Power P(z, S, α)", page_icon="📡", layout="wide")

FLUX_UNITS = {"Jy": 1.0, "mJy": 1e-3, "µJy": 1e-6}
MPC_M = 3.0856775814913673e22
PREFACTOR = 4 * np.pi * MPC_M**2 * 1e-26  # W/Hz per (Jy * Mpc^2) = 1.197e20


# ----------------------------------------------------------------------------
# The function P(z, S, alpha)
# ----------------------------------------------------------------------------
C_KMS = 299792.458
PRESETS = {  # flat LCDM (H0 [km/s/Mpc], Omega_m); radiation neglected
    "Planck18": (67.66, 0.30966),
    "Planck15": (67.74, 0.3075),
    "WMAP9": (69.32, 0.2865),
}


def get_cosmology(name, h0, om):
    return PRESETS.get(name, (h0, om))


def luminosity_distance_mpc(z, cosmo):
    """D_L = (1+z) c/H0 * integral_0^z dz'/E(z') for flat LCDM (numpy only)."""
    h0, om = cosmo
    z = np.asarray(z, float)
    flat = z.ravel()
    zmax = max(float(np.nanmax(flat)), 1e-6)
    grid = np.linspace(0.0, zmax, 4001)
    f = 1.0 / np.sqrt(om * (1 + grid) ** 3 + (1 - om))
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (f[1:] + f[:-1]) * np.diff(grid))])
    dc = C_KMS / h0 * np.interp(flat, grid, cum)  # comoving distance [Mpc]
    return ((1 + flat) * dc).reshape(z.shape)


def radio_power(s_jy, z, alpha, cosmo):
    """P(z, S, alpha) = 4 pi S D_L(z)^2 (1+z)^-(1+alpha)   [W/Hz], S ~ nu^alpha."""
    s_jy, z, alpha = np.broadcast_arrays(
        np.asarray(s_jy, float), np.asarray(z, float), np.asarray(alpha, float)
    )
    dl = luminosity_distance_mpc(z, cosmo)
    return PREFACTOR * s_jy * dl**2 * (1 + z) ** (-(1 + alpha))


# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
st.sidebar.header("Settings")
cosmo_name = st.sidebar.selectbox("Cosmology", ["Planck18", "Planck15", "WMAP9", "Custom flat ΛCDM"])
h0, om = 70.0, 0.3
if cosmo_name == "Custom flat ΛCDM":
    h0 = st.sidebar.number_input("H0 [km/s/Mpc]", value=70.0, min_value=1.0)
    om = st.sidebar.number_input("Ωm", value=0.30, min_value=0.0, max_value=1.0, step=0.01)
cosmo = get_cosmology(cosmo_name, h0, om)

flux_unit = st.sidebar.selectbox("Flux density unit", list(FLUX_UNITS), index=1)
conv = st.sidebar.radio(
    "Spectral index convention",
    ["S ∝ ν^α (α usually negative)", "S ∝ ν^-α (α usually positive)"],
)
sign = 1.0 if conv.startswith("S ∝ ν^α") else -1.0
unit_scale = FLUX_UNITS[flux_unit]

st.title("📡 Radio power as a function of z, S and α")
st.latex(r"P(z,S,\alpha) \;=\; 4\pi\, S\, D_L(z)^2\,(1+z)^{-(1+\alpha)}")
st.caption(
    "S is the observed flux density at the observing frequency, with S ∝ ν^α. "
    "P is the power at a rest-frame frequency equal to the observing frequency. "
    f"Cosmology: {cosmo_name}. In practical units: "
    "P [W/Hz] = 1.197×10²⁰ · S [Jy] · D_L² [Mpc²] · (1+z)^−(1+α)."
)

tab_calc, tab_z, tab_s, tab_a, tab_map = st.tabs(
    ["Calculator", "P vs z", "P vs S", "P vs α", "Map (z, S)"]
)

# ----------------------------------------------------------------------------
# Calculator
# ----------------------------------------------------------------------------
with tab_calc:
    c1, c2, c3 = st.columns(3)
    s_in = c1.number_input(f"Flux density S [{flux_unit}]", value=10.0, min_value=0.0, format="%.6g")
    z_in = c2.number_input("Redshift z", value=0.2, min_value=0.0, format="%.5f")
    a_in = c3.number_input("Spectral index α", value=-0.8, step=0.05, format="%.4f")

    if s_in <= 0 or z_in <= 0:
        st.info("Enter a flux density and a redshift above 0.")
    else:
        a_eff = sign * a_in
        dl = float(luminosity_distance_mpc(z_in, cosmo))
        kcorr = (1 + z_in) ** (-(1 + a_eff))
        p = float(radio_power(s_in * unit_scale, z_in, a_eff, cosmo))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("D_L [Mpc]", f"{dl:,.2f}")
        m2.metric("K-correction (1+z)^−(1+α)", f"{kcorr:.4f}")
        m3.metric("P [W/Hz]", f"{p:.3e}")
        m4.metric("log10 P", f"{np.log10(p):.3f}")

        st.markdown("**Step by step**")
        st.latex(
            rf"P = {PREFACTOR:.4e}\times {s_in * unit_scale:.4e}\ \mathrm{{Jy}}"
            rf"\times ({dl:,.2f}\ \mathrm{{Mpc}})^2 \times {kcorr:.4f}"
            rf"= {p:.3e}\ \mathrm{{W\,Hz^{{-1}}}}"
        )
        st.write(f"P in erg/s/Hz: **{p * 1e7:.3e}**")

# ----------------------------------------------------------------------------
# P vs z
# ----------------------------------------------------------------------------
with tab_z:
    a1, a2, a3 = st.columns(3)
    s_z = a1.number_input(f"Flux density S [{flux_unit}]", value=10.0, min_value=0.0, format="%.6g", key="s_z")
    z_rng = a2.slider("Redshift range", 0.01, 3.0, (0.01, 1.0), key="z_rng")
    al_z = a3.multiselect("α values", [-1.4, -1.2, -1.0, -0.8, -0.6, -0.4, 0.0],
                          default=[-1.0, -0.8, -0.6], key="al_z")
    if s_z > 0 and al_z:
        zs = np.linspace(z_rng[0], z_rng[1], 200)
        d = {f"α = {a}": np.log10(radio_power(s_z * unit_scale, zs, sign * a, cosmo)) for a in al_z}
        df = pd.DataFrame(d, index=pd.Index(zs, name="z"))
        st.line_chart(df, y_label="log10 P [W/Hz]")
        st.download_button("Download CSV", df.reset_index().to_csv(index=False).encode(),
                           "P_vs_z.csv", "text/csv")

# ----------------------------------------------------------------------------
# P vs S
# ----------------------------------------------------------------------------
with tab_s:
    b1, b2, b3 = st.columns(3)
    a_s = b1.number_input("Spectral index α", value=-0.8, step=0.05, format="%.3f", key="a_s")
    s_rng = b2.slider(f"log10 S [{flux_unit}]", -3.0, 4.0, (-1.0, 3.0), step=0.1, key="s_rng")
    z_s = b3.multiselect("Redshifts", [0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 2.0],
                         default=[0.1, 0.3, 0.5, 1.0], key="z_s")
    if z_s:
        logs = np.linspace(s_rng[0], s_rng[1], 200)
        s_vals = 10**logs * unit_scale
        d = {f"z = {z}": np.log10(radio_power(s_vals, z, sign * a_s, cosmo)) for z in z_s}
        df = pd.DataFrame(d, index=pd.Index(logs, name=f"log10 S [{flux_unit}]"))
        st.line_chart(df, y_label="log10 P [W/Hz]")
        st.caption("P ∝ S, so each curve is a straight line with slope 1.")

# ----------------------------------------------------------------------------
# P vs alpha
# ----------------------------------------------------------------------------
with tab_a:
    d1, d2, d3 = st.columns(3)
    s_a = d1.number_input(f"Flux density S [{flux_unit}]", value=10.0, min_value=0.0, format="%.6g", key="s_a")
    a_rng = d2.slider("α range", -2.0, 1.0, (-1.5, 0.0), step=0.05, key="a_rng")
    z_a = d3.multiselect("Redshifts", [0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 2.0],
                         default=[0.1, 0.5, 1.0, 2.0], key="z_a")
    if s_a > 0 and z_a:
        als = np.linspace(a_rng[0], a_rng[1], 200)
        d = {f"z = {z}": np.log10(radio_power(s_a * unit_scale, z, sign * als, cosmo)) for z in z_a}
        df = pd.DataFrame(d, index=pd.Index(als, name="α"))
        st.line_chart(df, y_label="log10 P [W/Hz]")
        st.caption("α only enters through the K-correction, so its effect grows with redshift.")

# ----------------------------------------------------------------------------
# 2D map
# ----------------------------------------------------------------------------
with tab_map:
    f1, f2, f3 = st.columns(3)
    a_m = f1.number_input("Spectral index α", value=-0.8, step=0.05, format="%.3f", key="a_m")
    z_m = f2.slider("Redshift range", 0.01, 3.0, (0.01, 1.5), key="z_m")
    s_m = f3.slider(f"log10 S [{flux_unit}]", -3.0, 4.0, (-1.0, 3.0), step=0.1, key="s_m")
    zg = np.linspace(z_m[0], z_m[1], 60)
    sg = np.linspace(s_m[0], s_m[1], 60)
    ZZ, SS = np.meshgrid(zg, sg)
    LP = np.log10(radio_power(10**SS * unit_scale, ZZ, sign * a_m, cosmo))
    grid = pd.DataFrame({"z": ZZ.ravel(), "logS": SS.ravel(), "logP": LP.ravel()})
    chart = (
        alt.Chart(grid)
        .mark_rect()
        .encode(
            x=alt.X("z:Q", bin=alt.Bin(maxbins=60), title="z"),
            y=alt.Y("logS:Q", bin=alt.Bin(maxbins=60), title=f"log10 S [{flux_unit}]"),
            color=alt.Color("mean(logP):Q", title="log10 P [W/Hz]", scale=alt.Scale(scheme="viridis")),
            tooltip=[alt.Tooltip("mean(logP):Q", title="log10 P", format=".2f")],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)

st.divider()
st.caption(
    "Check that S is in the unit selected in the sidebar and was measured at the observing frequency. "
    "With a photometric redshift, P is only approximate."
)