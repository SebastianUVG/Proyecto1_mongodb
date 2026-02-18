import { ObjectId } from "mongodb";

export interface MenuItem {
  restaurantId: ObjectId; // referenced
  name: string;
  price: number;
  category: string;
  tags: string[]; // multikey index
}
