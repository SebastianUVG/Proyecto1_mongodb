import { client } from "../config/database";
import { ObjectId } from "mongodb";

export const createOrderWithReview = async (
  userId: string,
  restaurantId: string,
  items: any[],
  review?: { rating: number; comment: string }
) => {
  const session = client.startSession();

  try {
    await session.withTransaction(async () => {
      const db = client.db("restaurant_system");

      const orderResult = await db.collection("orders").insertOne(
        {
          userId: new ObjectId(userId),
          restaurantId: new ObjectId(restaurantId),
          items,
          status: "completed",
          totalAmount: items.reduce((acc, i) => acc + i.price * i.quantity, 0),
          createdAt: new Date(),
        },
        { session }
      );

      if (review) {
        await db.collection("reviews").insertOne(
          {
            restaurantId: new ObjectId(restaurantId),
            userId: new ObjectId(userId),
            orderId: orderResult.insertedId,
            rating: review.rating,
            comment: review.comment,
            createdAt: new Date(),
          },
          { session }
        );
      }
    });

    console.log("✅ Transaction completed");
  } finally {
    await session.endSession();
  }
};
