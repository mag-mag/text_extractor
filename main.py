import streamlit as st
import requests
import json
import pandas as pd
import base64
import os
from PIL import Image

# To convert image format to WebP
def convert_to_webp(input_image, output_dir):
    # Open the input image
    img = Image.open(input_image)
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Get the input image filename
    input_filename = os.path.basename(input_image)
    # Construct the output file path
    output_filename = os.path.splitext(input_filename)[0] + ".webp"
    output_filepath = os.path.join(output_dir, output_filename)
    # Save the image as WebP
    img.save(output_filepath, "WebP")
    return output_filepath

#To remove commas from string
def remove_comma (number_str):
    num_int = int(number_str.replace(",", ""))
    return(num_int)

# Streamlit app
def main():
    st.title("Image to JSON Converter")
    
    # File uploader
    uploaded_file = st.file_uploader("Choose an image file", type=["png", "jpg", "jpeg"])
    st.image(uploaded_file)


    # Input fields
    OPENROUTER_API_KEY = st.text_input("OpenRouter API Key")
    productImageName_header = st.text_input("Product Name Header")
    productImageId_header = st.text_input("Product ID Header")
    priceImage_header = st.text_input("Price Header")
    
    if st.button("Process Image"):
        if uploaded_file is not None and OPENROUTER_API_KEY and productImageId_header and priceImage_header and productImageName_header:
            # Save uploaded image to a temporary file
            with open("temp_image.png", "wb") as f:
                f.write(uploaded_file.getvalue())

            # Convert image to WebP format
            output_dir = "images/WebP"
            webp_file = convert_to_webp("temp_image.png", output_dir)

            # Read the image file in binary mode
            with open(webp_file, "rb") as image_file:
                image_data = image_file.read()

            # Encode the image data to base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            data_base64 = "data:image/webp;base64," + encoded_image

            # Send request to API to extract text from image and convert it to a JSON.
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}"
                },
                data=json.dumps({
                    "model": "anthropic/claude-3-haiku",
                    "messages": [
                        {"role": "user", "content": [
                            {
                                "type" : "image_url",
                                "image_url" : {
                                    "url" : data_base64
                                }
                            },
                            {
                                "type" : "text",
                                "text" : "Extact data from the table."
                            }
                        ]},
                        {"role": "assistant", "content": "{"},
                        {"role": "system", "content": f'''
                            Use JSON format with the keys "ProductName", "productID" and "Price" and put ',' between each line of JSON except last line.
                            Image is in Farsi.
                            Extract columns value from following headers name in image:
                            "productID" : "{productImageId_header}",
                            "Price" : "{priceImage_header}",
                            "ProductName" : "{productImageName_header}"
                        '''},
                    ],
                    "temperature" : 0,
                    "response_format" : {
                        "type" : "json_object"
                    }
                })
            )

            #Clean a JSON string and prepare it to convert to a JSON.
            temp = response.json()['choices'][0]['message']['content']
            temp = "{"+temp
            new_text = temp.replace("\n", "")
            final_text = "["+new_text+"]"
            price_json = json.loads(final_text)
            price_pd = pd.DataFrame(price_json)
            price_pd['Price'] = price_pd['Price'].apply(remove_comma)
            print(price_pd['Price'][0])
            
            # Display the extracted data
            st.write("Extracted Data:")
            st.write(price_pd)
        else:
            st.warning("Please provide all the required inputs.")

if __name__ == "__main__":
    main()