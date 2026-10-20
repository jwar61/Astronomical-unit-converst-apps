import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="LAS to LLS converter", page_icon="🔭", layout="centered")

ARCSEC_TO_RAD = np.pi / 648000.0
LAS_UNITS = {"arcsec": 1.0, "arcmin": 60.0, "degree": 3600.0}
LLS_UNITS = {"pc": 1e6, "kpc": 1e3, "Mpc": 1.0}  # factor from Mpc


C_KMS = 299792.458
_ZGRID = np.linspace(0.0, 12.0, 48001)


@st.cache_data
def _dc_table(h0, om):
    """Comoving distance (Mpc) on a fine redshift grid, flat LCDM, no astropy needed."""
    f = 1.0 / np.sqrt(om * (1.0 + _ZGRID) ** 3 + (1.0 - om))
    cum = np.concatenate(([0.0], np.cumsum(0.5 * (f[1:] + f[:-1]) * np.diff(_ZGRID))))
    return (C_KMS / h0) * cum


def make_cosmo(h0, om):
    return (float(h0), float(om))


def d_a_mpc(z, cosmo):
    """Angular diameter distance in Mpc (works for scalars and arrays)."""
    h0, om = cosmo
    z = np.asarray(z, dtype=float)
    return np.interp(z, _ZGRID, _dc_table(h0, om)) / (1.0 + z)


def lls_mpc(las_arcsec, z, cosmo):
    """LLS = LAS[rad] x D_A, returned in Mpc."""
    return np.asarray(las_arcsec) * ARCSEC_TO_RAD * d_a_mpc(z, cosmo)


# ---------------------------------------------------------------- sidebar
st.title("LAS → LLS converter")
st.caption(
    "Converts the Largest Angular Size of a source to its Largest Linear "
    "(projected physical) Size using its redshift.  "
    "LLS = LAS[rad] × D_A(z)"
)

with st.sidebar:
    st.header("Cosmology (flat ΛCDM)")
    h0 = st.number_input("H₀ [km/s/Mpc]", 50.0, 100.0, 70.0, 0.1)
    om = st.number_input("Ω_m", 0.05, 1.0, 0.30, 0.01)
    st.write(f"Ω_Λ = {1 - om:.2f}")
    out_unit = st.selectbox("Output unit", list(LLS_UNITS), index=1)
    cosmo = make_cosmo(h0, om)
    st.markdown("---")
    st.caption(
        "Valid for roughly 0.0001 ≲ z ≲ 2 (radiation neglected). Below "
        "z ~ 0.001, peculiar velocities make redshift a poor distance indicator."
    )

tab1, tab2, tab3 = st.tabs(["Single source", "Batch (CSV)", "LLS vs redshift"])

# ------------------------------------------------------------ single source
with tab1:
    c1, c2 = st.columns(2)
    las_val = c1.number_input("LAS", min_value=0.0, value=60.0, step=1.0, format="%.4f")
    las_unit = c2.selectbox("LAS unit", list(LAS_UNITS))

    z = st.number_input(
        "Redshift z", min_value=1e-5, max_value=10.0, value=0.1, step=0.01, format="%.5f"
    )
    dz = st.number_input(
        "Redshift uncertainty σ_z (optional)", min_value=0.0, value=0.0, step=0.001, format="%.5f"
    )

    if z > 2:
        st.warning("z > 2: still computed, but outside the range this tool targets.")
    if z < 1e-3:
        st.warning("z < 0.001: peculiar velocities may dominate the distance error.")

    las_arcsec = las_val * LAS_UNITS[las_unit]
    f = LLS_UNITS[out_unit]
    da = d_a_mpc(z, cosmo)
    lls = float(lls_mpc(las_arcsec, z, cosmo)) * f
    scale_kpc_arcsec = da * 1e3 * ARCSEC_TO_RAD

    m1, m2, m3 = st.columns(3)
    m1.metric("D_A", f"{da:,.2f} Mpc")
    m2.metric("Scale", f"{scale_kpc_arcsec:.3f} kpc/″")
    m3.metric(f"LLS [{out_unit}]", f"{lls:,.4g}")

    if dz > 0:
        lo = float(lls_mpc(las_arcsec, max(z - dz, 1e-6), cosmo)) * f
        hi = float(lls_mpc(las_arcsec, z + dz, cosmo)) * f
        lo, hi = min(lo, hi), max(lo, hi)
        st.info(f"Range from z ± σ_z: {lo:,.4g} to {hi:,.4g} {out_unit}")

    st.caption(
        "This is the projected size. If the source axis is inclined to the sky "
        "plane, the true size is larger by 1/sin(i), so LLS is a lower limit."
    )

    with st.expander("Step-by-step values"):
        st.write(f"1. LAS = {las_arcsec:.4f} arcsec = {las_arcsec * ARCSEC_TO_RAD:.4e} rad")
        st.write(f"2. c/H₀ = {299792.458 / h0:,.2f} Mpc")
        dc = da * (1 + z)
        st.write(f"3. Comoving distance D_C = {dc:,.2f} Mpc")
        st.write(f"4. D_A = D_C / (1+z) = {da:,.2f} Mpc")
        st.write(f"5. LLS = LAS[rad] × D_A = {lls:,.4g} {out_unit}")

# -------------------------------------------------------------------- batch
with tab2:
    st.write("Upload a CSV with one column of LAS values and one column of redshifts.")
    up = st.file_uploader("CSV file", type=["csv"])
    if up is not None:
        df = pd.read_csv(up)
        cols = list(df.columns)
        b1, b2, b3 = st.columns(3)
        las_col = b1.selectbox("LAS column", cols, index=0)
        z_col = b2.selectbox("Redshift column", cols, index=min(1, len(cols) - 1))
        b_unit = b3.selectbox("LAS unit in file", list(LAS_UNITS), key="batch_unit")

        las_a = pd.to_numeric(df[las_col], errors="coerce") * LAS_UNITS[b_unit]
        zs = pd.to_numeric(df[z_col], errors="coerce")
        ok = las_a.notna() & zs.notna() & (zs > 0)

        res = df.copy()
        res["D_A_Mpc"] = np.nan
        res[f"LLS_{out_unit}"] = np.nan
        res.loc[ok, "D_A_Mpc"] = d_a_mpc(zs[ok].to_numpy(), cosmo)
        res.loc[ok, f"LLS_{out_unit}"] = (
            lls_mpc(las_a[ok].to_numpy(), zs[ok].to_numpy(), cosmo) * LLS_UNITS[out_unit]
        )

        if (~ok).any():
            st.warning(f"{int((~ok).sum())} row(s) skipped (missing or invalid values).")
        st.dataframe(res, use_container_width=True)
        st.download_button(
            "Download results (CSV)",
            res.to_csv(index=False).encode(),
            file_name="LLS_results.csv",
            mime="text/csv",
        )
    else:
        st.caption("Example format:  name,LAS,z")

# --------------------------------------------------------------------- curve
with tab3:
    las_c = st.number_input("LAS for the curve [arcsec]", 0.1, 10000.0, 60.0, key="curve_las")
    zg = np.logspace(-4, np.log10(2), 200)
    curve = pd.DataFrame(
        {"z": zg, f"LLS [{out_unit}]": lls_mpc(las_c, zg, cosmo) * LLS_UNITS[out_unit]}
    ).set_index("z")
    st.line_chart(curve)
    st.caption(
        "Beyond z ≈ 1 the curve flattens because D_A peaks near z ≈ 1.6 "
        "(for H₀ = 70, Ω_m = 0.3)."
    )