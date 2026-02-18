export interface Restaurant {
  name: string;
  description: string;
  category: string;
  location: {
    type: "Point";
    coordinates: [number, number]; // [lng, lat]
  };
  ratingAverage: number;
  createdAt: Date;
}
