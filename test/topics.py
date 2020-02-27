from google.cloud import pubsub_v1
from config import *


# project_id = "Your Google Cloud Project ID"
# topic_name = "Your Pub/Sub topic name"
def create_topic(project_id, topic_name):
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_name)

    topic = publisher.create_topic(topic_path)

    print("Topic created: {}".format(topic))


# project_id = "Your Google Cloud Project ID"
def get_topics(project_id):

    publisher = pubsub_v1.PublisherClient()
    project_path = publisher.project_path(project_id)

    for topic in publisher.list_topics(project_path):
        print(topic)

    return publisher.list_topics(project_path)


if __name__ == '__main__':
    if get_topics(PROJECT_ID_GMAIL):
        create_topic(PROJECT_ID_GMAIL, TOPIC_NAME_GMAIL)
