import streamlit as st
import base64


st.set_page_config(page_title="Astronomical Unit Converter")
st.title("Astronomical Unit Converter")

# DISTANCE CONVERSIONS 

class DistanceConverter:
    KM_PER_AU = 149597870.7
    AU_PER_LY = 63241.1
    LY_PER_PC = 3.26156

    def ly_to_parsec(self, ly):
        return ly / 3.26156

    def parsec_to_ly(self, pc):
        return pc * 3.26156

    def km_to_parsec(self, km):
        return km / (self.KM_PER_AU * self.AU_PER_LY * self.LY_PER_PC)

    def parsec_to_km(self, pc):
        return pc * self.LY_PER_PC * self.AU_PER_LY * self.KM_PER_AU

    def au_to_parsec(self, au):
        return au / (self.AU_PER_LY * self.LY_PER_PC)

    def parsec_to_au(self, pc):
        return pc * self.LY_PER_PC * self.AU_PER_LY


    def convert(self, conversion_type, value):
        conversions = {
            "Light-years → Parsecs": (self.ly_to_parsec, "parsecs"),
            "Parsecs → Light-years": (self.parsec_to_ly, "light-years"),
            "km → Parsecs": (self.km_to_parsec, "parsecs"),
            "Parsecs → km": (self.parsec_to_km, "km"),
            "AU → Parsecs": (self.au_to_parsec, "parsecs"),
            "Parsecs → AU": (self.parsec_to_au, "AU"),
        }
        func, unit = conversions[conversion_type]
        return func(value), unit



# ANGULAR CONVERSIONS CLASS 

class AngularConverter:

    def arcmin_to_arcsec(self, arcmin):
        return arcmin * 60

    def arcsec_to_arcmin(self, arcsec):
        return arcsec / 60
    
    def deg_to_arcsec(self, deg):
        return deg * 3600 

    def arcsec_to_deg(self, arcsec):
        return arcsec / 3600 

    def arcsec_to_parsec(self, arcsec):
            return 1 / (2*arcsec)

    def convert(self, conversion_type, value):
        conversions = {
            "Arcminutes → Arcseconds": (self.arcmin_to_arcsec, "arcseconds"),
            "Arcseconds → Arcminutes": (self.arcsec_to_arcmin, "arcminutes"),
            "Degrees → Arcseconds": (self.deg_to_arcsec, "arcseconds"),
            "Arcseconds → Degrees": (self.arcsec_to_deg, "degrees"),
            "2Arcseconds → Parsecs": (self.arcsec_to_parsec, "Parsecs"),
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
            "Light-years → Parsecs",
            "Parsecs → Light-years",
            "km → Parsecs",
            "Parsecs → km",
            "AU → Parsecs",
            "Parsecs → AU",
        ]
    )
else:
    converter = AngularConverter()
    conversion = st.selectbox(
        "Choose an angular conversion:",
        [
            "Arcminutes → Arcseconds",
            "Arcseconds → Arcminutes",
            "Degrees → Arcseconds",
            "Arcseconds → Degrees",
            "2Arcseconds → Parsecs",
        ]
    )

value = st.number_input("Enter value:")

if value < 0:
    st.write("impossible")
else :  
    if st.button("Convert"):
        result, unit = converter.convert(conversion, value)
        st.success(f"Result: {result} {unit}")