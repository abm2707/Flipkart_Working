from flask import Flask, render_template, request
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json
import os

app = Flask(__name__)

# Load the AFINN lexicon into memory as a dictionary
afinn_path = os.path.join(os.path.dirname(__file__), 'AFINN-111.txt')
with open(afinn_path, 'r') as f:
    afinn = dict(map(str.strip, line.split('\t')) for line in f)

# Define a function to calculate the sentiment score of a text using the AFINN lexicon
def calculate_sentiment(text):
    words = text.split()
    score = sum([int(afinn.get(word.lower(), 0)) for word in words])
    num_words = len(words)
    if num_words == 0:
        return 0
    else:
        sentiment = round(score/num_words, 2)
        return sentiment

# Define the route for the landing page
@app.route('/')
def index():
    return render_template('index.html')

# Define the route for the reviews page
@app.route('/reviews',methods = ['POST'])
def reviews():
    # Initialize a new firefox web driver
    driver = webdriver.Firefox()

    url= request.form['url']
    # Navigate to the Flipkart product page
    driver.get(url)

    # Close the login pop-up if it appears
    try:
        close_button = driver.find_element(By.XPATH, '//button[@class="_2KpZ6l _2doB4z"]')
        close_button.click()
        time.sleep(2)
    except:
        pass

    # Scroll to the bottom of the page repeatedly until all reviews are loaded
    while True:
        # Get the current page height
        current_height = driver.execute_script("return document.body.scrollHeight")

        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for the page to load
        time.sleep(2)

        # Get the new page height
        new_height = driver.execute_script("return document.body.scrollHeight")

        # If the page height has not increased, all reviews have been loaded
        if new_height == current_height:
            break

    # Extract all the review elements
    reviews = []
    while True:
        review_elements = driver.find_elements(By.XPATH, '//div[@class="_1AtVbE col-12-12"]')

        # Extract the text of each review element and determine the sentiment
        for review_element in review_elements:
            try:
                review_text = review_element.find_element(By.XPATH, './/div[contains(@class,"t-ZTKy")][1]').text
                review_sentiment = calculate_sentiment(review_text)
                sentiment_label = "positive" if review_sentiment > 0 else "negative" if review_sentiment < 0 else "neutral"
                reviews.append((review_text, review_sentiment, sentiment_label))
            except:
                pass

        # Click the "Next page" button
        try:
            next_button = driver.find_element(By.XPATH, '//span[normalize-space()="Next"]')
            next_button.click()

            # Wait for the page to load
            time.sleep(2)

        except:
            break

    # Close the web driver
    driver.quit()

    # Render the reviews template with the extracted reviews
    return render_template('reviews.html', reviews=reviews)

# Run the app on port 5000
if __name__ == '__main__':
    app.run(port=5000, debug=True)
