import streamlit as st
import numpy as np
from astropy.cosmology import FlatLambdaCDM
import astropy.units as u

st.set_page_config(page_title="Arcsecond → Parsec (vs Redshift)", page_icon="🌌")

st.title("🌌 Arcsecond → Parsec Converter (as a function of redshift)")

st.markdown(
    """
For **nearby, static** objects, 1 parsec is simply defined as the distance
at which 1 AU subtends 1 arcsecond, so *d (pc) = 1 / p (arcsec)*.

But for **cosmological distances** (redshift *z* > 0), this breaks down.
Instead, an angular size on the sky is converted to a physical size using
the **angular diameter distance** $D_A(z)$:
"""
)

st.latex(r"\ell = \theta \times D_A(z)")

st.markdown(
    r"""
where $\theta$ is the angle in **radians** and $\ell$ is the physical
(transverse) size, usually expressed in kpc or pc.
"""
)

st.divider()

# --- Cosmology parameters ---
st.subheader("Cosmology")
c1, c2, c3 = st.columns(3)
H0 = c1.number_input("H₀ (km/s/Mpc)", min_value=1.0, value=67.7, step=0.1)
Om0 = c2.number_input("Ωₘ", min_value=0.0, max_value=1.0, value=0.31, step=0.01)
Ode0 = c3.number_input("Ω_Λ (info only, flat assumed)", min_value=0.0, max_value=1.0, value=1 - 0.31, step=0.01, disabled=True)

cosmo = FlatLambdaCDM(H0=H0, Om0=Om0)

st.divider()

# --- Inputs ---
st.subheader("Input")
col1, col2 = st.columns(2)
arcsec = col1.number_input(
    "Angular size (arcseconds)",
    min_value=0.0,
    value=1.0,
    step=0.0001,
    format="%.6f",
)
z = col2.number_input(
    "Redshift z",
    min_value=0.0,
    value=1.0,
    step=0.01,
    format="%.4f",
)

# --- Conversion ---
if arcsec > 0:
    theta_rad = (arcsec * u.arcsec).to(u.rad).value

    if z == 0:
        # Local limit: d (pc) = 1 / p(arcsec)
        physical_pc = 1 / arcsec
        D_A_Mpc = None
    else:
        D_A = cosmo.angular_diameter_distance(z)  # Mpc
        D_A_Mpc = D_A.value
        physical_size = theta_rad * D_A  # Mpc (radian is dimensionless)
        physical_pc = physical_size.to(u.pc).value

    st.subheader("Result")
    if D_A_Mpc is not None:
        st.metric("Angular diameter distance D_A(z)", f"{D_A_Mpc:,.2f} Mpc")
    col1, col2 = st.columns(2)
    col1.metric("Physical size", f"{physical_pc:,.4g} pc")
    col2.metric("Physical size", f"{physical_pc/1e3:,.4g} kpc")

else:
    st.warning("Please enter an angular size greater than 0 arcseconds.")

st.divider()
st.caption(
    "Uses astropy's FlatLambdaCDM angular-diameter-distance calculation. "
    "At z → 0, results converge to the classical d(pc) = 1/p(arcsec) relation."
)