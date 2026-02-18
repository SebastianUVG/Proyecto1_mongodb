import { ObjectId } from "mongodb";

export interface Review {
  restaurantId: ObjectId;
  userId: ObjectId;
  orderId: ObjectId;
  rating: number;
  comment: string;
  createdAt: Date;
}
