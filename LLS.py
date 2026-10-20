import io

import numpy as np
import pandas as pd
import streamlit as st
import astropy.units as u
from astropy.cosmology import FlatLambdaCDM

st.set_page_config(page_title="Angular size to LLS", page_icon="🔭")
st.title("🔭 Angular size → Largest Linear Size (LLS)")
st.caption("LLS = θ × D_A(z), flat ΛCDM")

# ---------------- Sidebar: cosmology ----------------
st.sidebar.header("Cosmology")
H0 = st.sidebar.number_input("H0 [km/s/Mpc]", 50.0, 100.0, 70.0, 0.1)
Om0 = st.sidebar.number_input("Ω_m", 0.05, 1.0, 0.30, 0.01)
GRG_LIMIT = st.sidebar.number_input("Giant threshold [Mpc]", 0.1, 5.0, 0.7, 0.1)
cosmo = FlatLambdaCDM(H0=H0, Om0=Om0)
st.sidebar.write(f"Using H0={H0}, Ωm={Om0}, ΩΛ={1 - Om0:.2f}")

UNIT_TO_ARCSEC = {"arcsec": 1.0, "arcmin": 60.0, "degree": 3600.0}


def compute(z, theta_arcsec):
    z = np.asarray(z, dtype=float)
    theta = np.asarray(theta_arcsec, dtype=float) * u.arcsec
    d_a = cosmo.angular_diameter_distance(z)
    lls = (theta * d_a).to(u.Mpc, u.dimensionless_angles())
    scale = cosmo.kpc_proper_per_arcmin(z).to(u.kpc / u.arcsec)
    return d_a.to(u.Mpc), scale, lls


tab1, tab2 = st.tabs(["Single source", "Batch (CSV)"])

# ---------------- Single source ----------------
with tab1:
    c1, c2 = st.columns(2)
    z = c1.number_input("Redshift z", 0.0001, 10.0, 0.1, 0.001, format="%.4f")
    dz = c2.number_input("z uncertainty (optional)", 0.0, 1.0, 0.0, 0.001, format="%.4f")

    c3, c4 = st.columns(2)
    theta_val = c3.number_input("Angular size", 0.0, 100000.0, 120.0, 1.0)
    unit = c4.selectbox("Unit", list(UNIT_TO_ARCSEC))
    theta_arcsec = theta_val * UNIT_TO_ARCSEC[unit]

    d_a, scale, lls = compute(z, theta_arcsec)
    lls_mpc = float(lls.value)

    m1, m2, m3 = st.columns(3)
    m1.metric("D_A", f"{d_a.value:.1f} Mpc")
    m2.metric("Scale", f"{scale.value:.3f} kpc/″")
    m3.metric("LLS", f"{lls_mpc:.3f} Mpc")

    st.write(
        f"**LLS** = {lls_mpc * 1e3:,.1f} kpc = {lls_mpc * 1e6:,.0f} pc "
        f"= {lls_mpc * 1e6:.3e} pc"
    )

    if dz > 0:
        lo = compute(max(z - dz, 1e-6), theta_arcsec)[2].value
        hi = compute(z + dz, theta_arcsec)[2].value
        st.write(f"LLS range for z ± Δz: {min(lo, hi):.3f} – {max(lo, hi):.3f} Mpc")

    if lls_mpc >= GRG_LIMIT:
        st.success(f"Giant radio galaxy candidate (LLS ≥ {GRG_LIMIT} Mpc)")
    else:
        st.info(f"Below the {GRG_LIMIT} Mpc giant threshold")

# ---------------- Batch ----------------
with tab2:
    st.write(
        "Upload a CSV with columns **z** and **theta_arcsec** "
        "(an optional **name** column is kept)."
    )
    file = st.file_uploader("CSV file", type="csv")
    if file is not None:
        df = pd.read_csv(file)
        missing = {"z", "theta_arcsec"} - set(df.columns)
        if missing:
            st.error(f"Missing column(s): {', '.join(sorted(missing))}")
        else:
            d_a, scale, lls = compute(df["z"].values, df["theta_arcsec"].values)
            df["D_A_Mpc"] = d_a.value
            df["scale_kpc_per_arcsec"] = scale.value
            df["LLS_Mpc"] = lls.value
            df["LLS_pc"] = lls.value * 1e6
            df["giant"] = df["LLS_Mpc"] >= GRG_LIMIT
            st.dataframe(df, use_container_width=True)

            buf = io.StringIO()
            df.to_csv(buf, index=False)
            st.download_button("Download results", buf.getvalue(), "lls_results.csv", "text/csv")