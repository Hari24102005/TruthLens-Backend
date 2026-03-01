# Use Python 3.10
FROM python:3.10

# Set the working directory
WORKDIR /code

# Copy your requirements and install them
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy your app code
COPY . .

# Run the Flask server on port 7860 (Hugging Face default)
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "app:app"]
