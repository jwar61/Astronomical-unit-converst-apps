import streamlit as st

st.set_page_config(page_title="Astronomical Unit Converter")
st.title("Astronomical Unit Converter")

# DISTANCE CONVERSIONS 

class DistanceConverter:
    def Km_to_AU(self, Km):
        return Km/149597870.7
    
    def AU_to_Km(self, AU):
        return AU*149597870.7

    def AU_to_Ly(self, AU):
        return AU/63241.1

    def Ly_to_AU(self, Ly):
        return Ly*63241.1

    def Ly_to_parsec(self, Ly):
        return Ly/3.26156

    def parsec_to_ly(self, PC):
        return PC*3.26156

    def convert(self, conversion_type, value):
        conversions = {
            "Km → AU": (self.Km_to_AU, "AU"),
            "AU → Km": (self.AU_to_Km, "km"),
            "AU → Light-years": (self.UA_to_Ly, "light-years"),
            "Light-years → AU": (self.Ly_to_AU, "AU"),
            "Light-years → Parsecs": (self.Ly_to_parsec, "parsecs"),
            "Parsecs → Light-years": (self.parsec_to_Ly, "light-years"),
        }
        func, unit = conversions[conversion_type]
        return func(value), unit


# ANGULAR CONVERSIONS CLASS 

class AngularConverter:
    def deg_to_arcmin(self, deg):
        return deg * 60

    def arcmin_to_deg(self, arcmin):
        return arcmin / 60

    def arcmin_to_arcsec(self, arcmin):
        return arcmin * 60

    def arcsec_to_arcmin(self, arcsec):
        return arcsec / 60

    def convert(self, conversion_type, value):
        conversions = {
            "Degrees → Arcminutes": (self.deg_to_arcmin, "arcminutes"),
            "Arcminutes → Degrees": (self.arcmin_to_deg, "degrees"),
            "Arcminutes → Arcseconds": (self.arcmin_to_arcsec, "arcseconds"),
            "Arcseconds → Arcminutes": (self.arcsec_to_arcmin, "arcminutes"),
        }
        func, unit = conversions[conversion_type]
        return func(value), unit


conversion_category = st.selectbox(
    "Choose conversion category:",
    ("Distance", "Angular")
)

if conversion_category == "Distance":
    converter = DistanceConverter()
    conversion = st.selectbox(
        "Choose a distance conversion:",
        [
            "km → AU",
            "AU → km",
            "AU → Light-years",
            "Light-years → AU",
            "Light-years → Parsecs",
            "Parsecs → Light-years",
        ]
    )
else:
    converter = AngularConverter()
    conversion = st.selectbox(
        "Choose an angular conversion:",
        [
            "Degrees → Arcminutes",
            "Arcminutes → Degrees",
            "Arcminutes → Arcseconds",
            "Arcseconds → Arcminutes",
        ]
    )

value = st.number_input("Enter value:")

if st.button("Convert"):
    result, unit = converter.convert(conversion, value)
    st.success(f"Result: {result} {unit}")