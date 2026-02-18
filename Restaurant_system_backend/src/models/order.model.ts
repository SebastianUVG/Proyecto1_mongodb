import { ObjectId } from "mongodb";

export interface Order {
  userId: ObjectId;
  restaurantId: ObjectId;
  items: {
    menuItemId: ObjectId;
    name: string;
    quantity: number;
    price: number;
  }[];
  status: "pending" | "completed" | "cancelled";
  totalAmount: number;
  createdAt: Date;
}
