import io

import numpy as np
import pandas as pd
import streamlit as st
from astropy import units as u
from astropy.cosmology import FlatLambdaCDM, Planck15, Planck18, WMAP9

st.set_page_config(page_title="Radio Power Calculator", page_icon="📡", layout="wide")

FLUX_UNITS = {"Jy": 1.0, "mJy": 1e-3, "µJy": 1e-6}
FREQ_UNITS = {"MHz": 1e6, "GHz": 1e9, "Hz": 1.0}


# ----------------------------------------------------------------------------
# Physics
# ----------------------------------------------------------------------------
def get_cosmology(name, h0, om):
    if name == "Planck18":
        return Planck18
    if name == "Planck15":
        return Planck15
    if name == "WMAP9":
        return WMAP9
    return FlatLambdaCDM(H0=h0, Om0=om)


def radio_power(s_jy, z, alpha, nu_obs_hz, nu_rest_hz, cosmo):
    """Radio power in W/Hz at rest-frame frequency nu_rest.

    P = 4 pi D_L^2 S_obs (nu_rest / nu_obs)^alpha / (1+z)^(1+alpha),
    with the convention S ~ nu^alpha. If nu_rest = nu_obs this reduces to
    P = 4 pi D_L^2 S / (1+z)^(1+alpha).
    """
    s_jy, z, alpha = np.broadcast_arrays(
        np.asarray(s_jy, float), np.asarray(z, float), np.asarray(alpha, float)
    )
    dl_m = cosmo.luminosity_distance(z).to(u.m).value
    s_si = s_jy * 1e-26  # Jy -> W m^-2 Hz^-1
    p = 4 * np.pi * dl_m**2 * s_si * (nu_rest_hz / nu_obs_hz) ** alpha / (1 + z) ** (1 + alpha)
    return p, dl_m / 3.0856775814913673e22  # P [W/Hz], D_L [Mpc]


def flux_from_power(p_whz, z, alpha, nu_obs_hz, nu_rest_hz, cosmo):
    """Inverse of radio_power: observed flux density in Jy."""
    dl_m = cosmo.luminosity_distance(z).to(u.m).value
    s_si = p_whz * (1 + z) ** (1 + alpha) / (4 * np.pi * dl_m**2 * (nu_rest_hz / nu_obs_hz) ** alpha)
    return s_si / 1e-26


def kpc_per_arcsec(z, cosmo):
    return cosmo.kpc_proper_per_arcmin(z).to(u.kpc / u.arcsec).value


# ----------------------------------------------------------------------------
# Sidebar: settings shared by all tabs
# ----------------------------------------------------------------------------
st.sidebar.header("Settings")

cosmo_name = st.sidebar.selectbox("Cosmology", ["Planck18", "Planck15", "WMAP9", "Custom flat ΛCDM"])
h0, om = 70.0, 0.3
if cosmo_name == "Custom flat ΛCDM":
    h0 = st.sidebar.number_input("H0 [km/s/Mpc]", value=70.0, min_value=1.0)
    om = st.sidebar.number_input("Ωm", value=0.30, min_value=0.0, max_value=1.0, step=0.01)
cosmo = get_cosmology(cosmo_name, h0, om)

flux_unit = st.sidebar.selectbox("Flux density unit", list(FLUX_UNITS), index=0)
freq_val = st.sidebar.number_input("Observing frequency", value=1.4, min_value=0.0, format="%.6g")
freq_unit = st.sidebar.selectbox("Frequency unit", list(FREQ_UNITS), index=1)
nu_obs = freq_val * FREQ_UNITS[freq_unit]

convention = st.sidebar.radio(
    "Spectral index convention",
    ["S ∝ ν^α (α usually negative)", "S ∝ ν^-α (α usually positive)"],
)
sign = 1.0 if convention.startswith("S ∝ ν^α") else -1.0

rest_mode = st.sidebar.radio(
    "Output frequency",
    ["Same as observing frequency (K-correction only)", "Fixed rest-frame frequency"],
)
if rest_mode.startswith("Fixed"):
    rest_val = st.sidebar.number_input("Rest-frame frequency", value=1.4, min_value=0.0, format="%.6g")
    rest_unit = st.sidebar.selectbox("Rest-frame unit", list(FREQ_UNITS), index=1)
    nu_rest = rest_val * FREQ_UNITS[rest_unit]
else:
    nu_rest = nu_obs

default_alpha = st.sidebar.number_input(
    "Default α (used when a batch row has none)", value=-0.8, step=0.05, format="%.3f"
)

st.title("📡 Radio Power Calculator")
st.caption(
    "P = 4π D_L² S_obs (ν_rest/ν_obs)^α / (1+z)^(1+α)  [W/Hz], with S ∝ ν^α. "
    f"Cosmology: {cosmo_name}."
)

tab1, tab2, tab3 = st.tabs(["Single source", "Batch table", "Power → flux"])

# ----------------------------------------------------------------------------
# Tab 1: single source
# ----------------------------------------------------------------------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    s_in = c1.number_input(f"Flux density [{flux_unit}]", value=10.0, min_value=0.0, format="%.6g")
    z_in = c2.number_input("Redshift z", value=0.2, min_value=0.0, format="%.5f")
    a_in = c3.number_input("Spectral index α", value=-0.8, step=0.05, format="%.4f")
    las_in = c4.number_input("LAS [arcsec] (optional)", value=0.0, min_value=0.0, format="%.4g")

    if z_in <= 0 or s_in <= 0:
        st.info("Enter a flux density and a redshift above 0.")
    else:
        p, dl = radio_power(s_in * FLUX_UNITS[flux_unit], z_in, sign * a_in, nu_obs, nu_rest, cosmo)
        p, dl = float(p), float(dl)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("D_L [Mpc]", f"{dl:,.2f}")
        m2.metric("P [W/Hz]", f"{p:.3e}")
        m3.metric("log10 P [W/Hz]", f"{np.log10(p):.2f}")
        m4.metric("P [erg/s/Hz]", f"{p * 1e7:.3e}")
        if las_in > 0:
            scale = float(kpc_per_arcsec(z_in, cosmo))
            st.write(
                f"Scale: **{scale:.3f} kpc/arcsec** → projected size "
                f"**{las_in * scale:,.1f} kpc** ({las_in * scale / 1000:.3f} Mpc)"
            )

# ----------------------------------------------------------------------------
# Tab 2: batch
# ----------------------------------------------------------------------------
with tab2:
    st.write(
        "Edit the table, add rows, or upload a CSV with columns "
        "`name, S, z, alpha, LAS_arcsec` (S in the flux unit chosen in the sidebar). "
        "Rows without a redshift are skipped."
    )
    default_df = pd.DataFrame(
        {
            "name": [f"eRGs{i}" for i in range(1, 10)],
            "S": [1.3815e-2, 2.6389e-2, 2.1282e-2, 2.6847e-2, np.nan, 7.3730e-1, 3.2128e-2, 3.9462e-2, 4.8624e-3],
            "z": [np.nan] * 9,
            "alpha": [-0.929457, -0.97647, -0.852498, -0.851705, -0.826112, -0.802816, -1.006642, -0.384574, -0.802816],
            "LAS_arcsec": [92.86377, 110.60685, 81.17915, 95.2811, np.nan, 617.03489, 86.952489, 86.6267, 79.257],
        }
    )
    up = st.file_uploader("Upload CSV (optional)", type=["csv", "txt", "tsv"])
    if up is not None:
        raw = up.getvalue().decode("utf-8", errors="ignore")
        sep = "\t" if "\t" in raw.splitlines()[0] else ","
        df_in = pd.read_csv(io.StringIO(raw), sep=sep)
        df_in.columns = [c.strip() for c in df_in.columns]
        for col in ["name", "S", "z", "alpha", "LAS_arcsec"]:
            if col not in df_in.columns:
                df_in[col] = np.nan if col != "name" else ""
        default_df = df_in[["name", "S", "z", "alpha", "LAS_arcsec"]]

    edited = st.data_editor(default_df, num_rows="dynamic", use_container_width=True, key="batch")

    df = edited.copy()
    for col in ["S", "z", "alpha", "LAS_arcsec"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["alpha"] = df["alpha"].fillna(default_alpha)
    valid = (df["S"] > 0) & (df["z"] > 0)

    out = pd.DataFrame({"name": df["name"]})
    out["S_Jy"] = df["S"] * FLUX_UNITS[flux_unit]
    out["z"] = df["z"]
    out["alpha"] = df["alpha"]
    out["D_L_Mpc"] = np.nan
    out["P_W_per_Hz"] = np.nan
    out["log10_P"] = np.nan
    out["size_kpc"] = np.nan
    if valid.any():
        p, dl = radio_power(
            out.loc[valid, "S_Jy"].values,
            out.loc[valid, "z"].values,
            sign * out.loc[valid, "alpha"].values,
            nu_obs,
            nu_rest,
            cosmo,
        )
        out.loc[valid, "D_L_Mpc"] = dl
        out.loc[valid, "P_W_per_Hz"] = p
        out.loc[valid, "log10_P"] = np.log10(p)
        las = df.loc[valid, "LAS_arcsec"].values
        out.loc[valid, "size_kpc"] = las * kpc_per_arcsec(out.loc[valid, "z"].values, cosmo)

    st.subheader("Results")
    st.dataframe(
        out.style.format(
            {
                "S_Jy": "{:.4e}",
                "z": "{:.4f}",
                "alpha": "{:.3f}",
                "D_L_Mpc": "{:,.1f}",
                "P_W_per_Hz": "{:.3e}",
                "log10_P": "{:.2f}",
                "size_kpc": "{:,.1f}",
            },
            na_rep="-",
        ),
        use_container_width=True,
    )
    st.download_button(
        "Download results (CSV)",
        out.to_csv(index=False).encode(),
        file_name="radio_power_results.csv",
        mime="text/csv",
    )
    if (~valid).any():
        st.caption(f"{int((~valid).sum())} row(s) skipped (missing flux or redshift).")

# ----------------------------------------------------------------------------
# Tab 3: inverse
# ----------------------------------------------------------------------------
with tab3:
    st.write("Find the observed flux density that corresponds to a given radio power.")
    d1, d2, d3 = st.columns(3)
    logp = d1.number_input("log10 P [W/Hz]", value=25.0, step=0.1, format="%.2f")
    zi = d2.number_input("Redshift z ", value=0.2, min_value=0.0, format="%.5f")
    ai = d3.number_input("Spectral index α ", value=-0.8, step=0.05, format="%.4f")
    if zi > 0:
        s_jy = float(flux_from_power(10**logp, zi, sign * ai, nu_obs, nu_rest, cosmo))
        st.metric(f"Observed flux density [{flux_unit}]", f"{s_jy / FLUX_UNITS[flux_unit]:.4e}")
    else:
        st.info("Enter a redshift above 0.")

st.divider()
st.caption(
    "Check the units of your flux column (Jy vs mJy) and the frequency it was measured at. "
    "Photometric redshifts give approximate luminosities."
)