FROM python

WORKDIR var/www/html

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "gateway.py"]