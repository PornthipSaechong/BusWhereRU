Deploy to cloud:
gcloud app deploy /Users/pornthip/Documents/SIDE\ PROJECTS/BusWhereRU/app.yaml --project=buswhereru --version 1

Run dev server:
Desktop/gae/google-cloud-sdk/bin/dev_appserver.py /Users/pornthip/Documents/SIDE\ PROJECTS/BusWhereRU/app.yaml

Deploy custom taskqueue(everytime queue.yaml is updated):
gcloud app deploy /Users/pornthip/Documents/SIDE\ PROJECTS/BusWhereRU/queue.yaml
