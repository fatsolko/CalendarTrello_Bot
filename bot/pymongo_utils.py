import os
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()


MONGODB_LOGIN = os.getenv('MONGODB_LOGIN')

# Create the client
client = MongoClient(f"mongodb+srv://{MONGODB_LOGIN}"
                     f"@clusterbotequip.aj1qm.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

# Connect to our database
db = client['CalendarTrello']


def insert_document(collection, data):
    """ Function to insert a document into a collection and
    return the document's id.
    """
    return collection.insert_one(data).inserted_id


def set_user_db_data(file, data):
    """ Function to set a data into a document and
        return the document's id.
        """
    collection = db['user']
    return collection.update_one({"chat_id": str(file)}, {"$set": data}, upsert=True)


def get_creds_db_data(chat_id, data):
    """ Function to set a data into a document and
        return the document's id.
        """
    collection = db['user creds']
    return collection.find_one({"chat_id": str(chat_id)})[data]


def get_user_db_data(chat_id, data):
    """ Function to set a data into a document and
        return the document's id.
        """
    collection = db['user']
    return collection.find_one({"chat_id": str(chat_id)})[data]


def set_creds_db_data(file, data):
    """ Function to set a data into a document and
        return the document's id.
        """
    creds_collection = db['user creds']
    return creds_collection.update_one({'ip': file}, {"$set": data}, upsert=True)


def get_google_token(chat_id):
    """ Function to set a data into a document and
        return the document's id.
        """
    collection = db['user creds']
    return collection.find_one({"chat_id": str(chat_id)})

# print(insert_document(series_collection, new_show))
