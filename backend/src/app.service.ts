import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';
import { Readable } from 'stream';

@Injectable()
export class AppService {
  constructor(private readonly httpService: HttpService) {}

  async getChatStream(question: string, chatHistory: any[]): Promise<Readable> {
    // Gọi sang Python Service (Port 8000)
    const pythonApiUrl = 'http://localhost:8000/chat';

    try {
      const response = await lastValueFrom(
        this.httpService.post(
          pythonApiUrl, 
          { question, chat_history: chatHistory }, 
          { responseType: 'stream' }
        )
      );
      return response.data;
    } catch (error) {
      // Trả về stream thông báo lỗi
      const errStream = new Readable();
      errStream.push(`data: {"type": "error", "content": "Lỗi kết nối AI Service: ${error.message}"}\n\n`);
      errStream.push(null);
      return errStream;
    }
  }
}