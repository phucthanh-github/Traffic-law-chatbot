import { Controller, Post, Body } from '@nestjs/common';
import { AppService } from './app.service';

@Controller('chat')
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Post()
  async chat(@Body('question') question: string) {
    return this.appService.getChatResponse(question);
  }
}