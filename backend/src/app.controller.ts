import { Controller, Post, Body, Res } from '@nestjs/common';
import { AppService } from './app.service';
import * as express from 'express';

@Controller('chat')
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Post()
  async chat(
    @Body('question') question: string,
    @Body('chatHistory') chatHistory: any[],
    @Res() res: express.Response
  ) {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    try {
      const stream = await this.appService.getChatStream(question, chatHistory || []);
      stream.pipe(res);
    } catch (err) {
      res.write(`data: {"type": "error", "content": "${err.message}"}\n\n`);
      res.end();
    }
  }
}