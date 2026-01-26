import { NestFactory } from '@nestjs/core'; // <--- Dòng này để import NestFactory
import { AppModule } from './app.module';   // <--- Dòng này để import AppModule

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  
  // Bật CORS để Frontend (Next.js) có thể gọi API này
  app.enableCors(); 
  
  // Chạy server ở cổng 4000
  await app.listen(4000);
}
bootstrap();