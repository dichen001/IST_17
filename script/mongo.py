from pymongo import MongoClient
client = MongoClient()
db = client.test
coll = db.dataset


cursor = db.restaurants.find()


cursor = db.restaurants.find({"borough": "Manhattan"})
print cursor.count()
cursor = db.restaurants.find({"address.zipcode": "10075"})
cursor = db.restaurants.find({"grades.grade": "B"})
cursor = db.restaurants.find({"grades.score": {"$gt": 30}})
cursor = db.restaurants.find({"grades.score": {"$lt": 10}})
cursor = db.restaurants.find({"cuisine": "Italian", "address.zipcode": "10075"})
cursor = db.restaurants.find(
    {"$or": [{"cuisine": "Italian"}, {"address.zipcode": "10075"}]})
cursor = db.restaurants.find().sort([
    ("borough", pymongo.ASCENDING),
    ("address.zipcode", pymongo.ASCENDING)
])
cursor = db.restaurants.aggregate(
    [
        {"$group": {"_id": "$borough", "count": {"$sum": 1}}}
    ]
)

cursor = db.restaurants.aggregate(
    [
        {"$match": {"borough": "Queens", "cuisine": "Brazilian"}},
        {"$group": {"_id": "$address.zipcode", "count": {"$sum": 1}}}
    ]
)
for document in cursor:
    print(document)
print 'hi'