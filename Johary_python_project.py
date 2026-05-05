import streamlit as st
import base64

st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://assets.science.nasa.gov/dynamicimage/assets/science/psd/solar/2023/09/o/OSS.jpg?w=2925&h=2229&fit=clip&crop=faces%2Cfocalpoint");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.set_page_config(page_title="Astronomical Unit Converter")
st.title("Astronomical Unit Converter")

# DISTANCE CONVERSIONS 

class DistanceConverter:
    KM_PER_AU = 149597870.7
    AU_PER_LY = 63241.1
    LY_PER_PC = 3.26156

    def km_to_au(self, km):
        return km / 149597870.7

    def au_to_km(self, au):
        return au * 149597870.7

    def au_to_ly(self, au):
        return au / 63241.1

    def ly_to_au(self, ly):
        return ly * 63241.1

    def ly_to_parsec(self, ly):
        return ly / 3.26156

    def parsec_to_ly(self, pc):
        return pc * 3.26156
    
    def km_to_ly(self, km):
        return km / (self.KM_PER_AU * self.AU_PER_LY)

    def ly_to_km(self, ly):
        return ly * self.AU_PER_LY * self.KM_PER_AU

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
            "km → AU": (self.km_to_au, "AU"),
            "AU → km": (self.au_to_km, "km"),
            "AU → Light-years": (self.au_to_ly, "light-years"),
            "Light-years → AU": (self.ly_to_au, "AU"),
            "Light-years → Parsecs": (self.ly_to_parsec, "parsecs"),
            "Parsecs → Light-years": (self.parsec_to_ly, "light-years"),
            "km → Light-years": (self.km_to_ly, "light-years"),
            "Light-years → km": (self.ly_to_km, "km"),
            "km → Parsecs": (self.km_to_parsec, "parsecs"),
            "Parsecs → km": (self.parsec_to_km, "km"),
            "AU → Parsecs": (self.au_to_parsec, "parsecs"),
            "Parsecs → AU": (self.parsec_to_au, "AU"),
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
    
    def deg_to_arcsec(self, deg):
        return deg * 3600 

    def arcsec_to_deg(self, arcsec):
        return arcsec / 3600

    def convert(self, conversion_type, value):
        conversions = {
            "Degrees → Arcminutes": (self.deg_to_arcmin, "arcminutes"),
            "Arcminutes → Degrees": (self.arcmin_to_deg, "degrees"),
            "Arcminutes → Arcseconds": (self.arcmin_to_arcsec, "arcseconds"),
            "Arcseconds → Arcminutes": (self.arcsec_to_arcmin, "arcminutes"),
            "Degrees → Arcseconds": (self.deg_to_arcsec, "arcseconds"),
            "Arcseconds → Degrees": (self.arcsec_to_deg, "degrees"),
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
            "km → Light-years",
            "Light-years → km",
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
            "Degrees → Arcminutes",
            "Arcminutes → Degrees",
            "Arcminutes → Arcseconds",
            "Arcseconds → Arcminutes",
            "Degrees → Arcseconds",
            "Arcseconds → Degrees",
        ]
    )

value = st.number_input("Enter value:")

if value < 0:
    st.write("impossible")
else :  
    if st.button("Convert"):
        result, unit = converter.convert(conversion, value)
        st.success(f"Result: {result} {unit}")