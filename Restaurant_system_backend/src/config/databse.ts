import { MongoClient, Db } from "mongodb";
import dotenv from "dotenv";

dotenv.config();

const uri = process.env.MONGO_URI as string;

export const client = new MongoClient(uri);

let db: Db;

export const connectDB = async () => {
  await client.connect();
  db = client.db("restaurant_system");
  console.log("✅ Connected to MongoDB");
};

export const getDB = () => db;
