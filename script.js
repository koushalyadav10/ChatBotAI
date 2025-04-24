require('dotenv').config();
const express = require('express');
const { GoogleGenerativeAI } = require('@google/generative-ai');
const cors = require('cors');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Initialize Google Generative AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

// Chat endpoint
app.post('/api/chat', async (req, res) => {
    try {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        
        // Combine system message with conversation history
        const chat = model.startChat({
            history: req.body.messages,
            generationConfig: {
                maxOutputTokens: 500,
            },
        });
        
        const result = await chat.sendMessage(req.body.messages[req.body.messages.length - 1].content);
        const response = await result.response;
        const text = response.text();
        
        res.json({ response: text });
    } catch (error) {
        console.error("Error:", error);
        res.status(500).json({ error: "Error processing your request" });
    }
});

// Start server
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});