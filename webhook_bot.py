import os
import logging
from flask import Flask

app = Flask(__name__)

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def home():
    return 'Bot is running!', 200