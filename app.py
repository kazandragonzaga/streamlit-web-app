import streamlit as st

# Title ng app
st.title("My First Web App 💻")

# Text input
name = st.text_input("Enter your name:")

# Number input
age = st.number_input("Enter your age:", min_value=1, max_value=100)

# Button
if st.button("Submit"):
    st.write(f"Hello {name}! You are {age} years old.")

# Checkbox
if st.checkbox("Show fun fact"):
    st.write("Fun fact: Streamlit makes Python web apps super easy! 😎")