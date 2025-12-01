import os
import sys
from pymongo import MongoClient

def main():
    uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    dbname = os.getenv('MONGO_DBNAME', 'timetable')
    try:
        client = MongoClient(uri)
        db = client[dbname]
    except Exception as e:
        print('Failed to connect to MongoDB:', e)
        sys.exit(1)

    print(f'Connected to MongoDB: {uri}  (database: {dbname})')
    cols = db.list_collection_names()
    if not cols:
        print('No collections found in database yet.')
        return

    for coll in cols:
        try:
            count = db[coll].count_documents({})
            print(f'Collection: {coll} — {count} documents')
            sample = db[coll].find_one()
            print(' Sample document:')
            print(sample)
        except Exception as e:
            print(f' Error reading collection {coll}:', e)
        print('-' * 60)

if __name__ == '__main__':
    main()
