FROM python:alpine3.7 
COPY ./API /app/API
COPY ./MHIST /app/MHIST
COPY ./GENHIST /app/GENHIST
COPY ./STHOLES /app/STHOLES
COPY requirements.txt /app/
COPY utils.py /app/
WORKDIR /app/API
RUN pip install --upgrade pip
RUN pip install -r ../requirements.txt 
EXPOSE 5000 
ENTRYPOINT [ "python" ] 
CMD [ "main.py" ] 

