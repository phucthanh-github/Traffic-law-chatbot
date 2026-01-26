import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { lastValueFrom } from 'rxjs';

@Injectable()
export class AppService {
  constructor(private readonly httpService: HttpService) {}

  async getChatResponse(question: string) {
    // Gọi sang Python Service (Port 8000)
    const pythonApiUrl = 'http://localhost:8000/chat';

    try {
      const response = await lastValueFrom(
        this.httpService.post(pythonApiUrl, { question })
      );
      return response.data;
    } catch (error) {
      return { answer: "Lỗi kết nối AI Service", steps: [] };
    }
  }
}