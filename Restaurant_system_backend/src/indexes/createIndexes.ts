import { getDB } from "../config/database";

export const createIndexes = async () => {
  const db = getDB();

  // 1️⃣ Simple Index
  await db.collection("users").createIndex({ email: 1 }, { unique: true });

  // 2️⃣ Compound Index
  await db.collection("orders").createIndex(
    { restaurantId: 1, createdAt: -1 }
  );

  // 3️⃣ Multikey Index
  await db.collection("menuItems").createIndex({ tags: 1 });

  // 4️⃣ Geospatial Index
  await db.collection("restaurants").createIndex({ location: "2dsphere" });

  // 5️⃣ Text Index
  await db.collection("restaurants").createIndex({
    name: "text",
    description: "text",
  });

  console.log("✅ Indexes created");
};
