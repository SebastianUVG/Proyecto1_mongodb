import { getDB } from "../config/database";

export const topRatedRestaurants = async () => {
  const db = getDB();

  return db.collection("reviews").aggregate([
    {
      $group: {
        _id: "$restaurantId",
        avgRating: { $avg: "$rating" },
        totalReviews: { $sum: 1 }
      }
    },
    {
      $sort: { avgRating: -1 }
    },
    {
      $limit: 5
    },
    {
      $lookup: {
        from: "restaurants",
        localField: "_id",
        foreignField: "_id",
        as: "restaurant"
      }
    }
  ]).toArray();
};
