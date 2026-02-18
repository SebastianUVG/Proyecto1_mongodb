import app from "./app";
import { connectDB } from "./config/database";
import { createIndexes } from "./indexes/createIndexes";

const PORT = 3000;

const startServer = async () => {
  await connectDB();
  await createIndexes();

  app.listen(PORT, () => {
    console.log(`🚀 Server running on port ${PORT}`);
  });
};

startServer();
