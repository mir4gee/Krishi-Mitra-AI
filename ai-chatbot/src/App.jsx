

import { useState, useRef, useEffect } from 'react';
import { User, Mic, Square, Send, Bot, ArrowRight, ArrowLeft, MessageCircle } from 'lucide-react';

const WelcomePage = ({ onSelectPerson }) => {
  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-6">
            <MessageCircle className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Welcome to AI Krishi Chatbot</h1>
          <p className="text-xl text-gray-600">Choose your profile to get started</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {/* Sell - Farmers */}
          <div 
            onClick={() => onSelectPerson('person1')}
            className="group cursor-pointer transform hover:scale-105 transition-all duration-300"
          >
            <div className="bg-white rounded-2xl shadow-lg hover:shadow-2xl p-8 text-center border-2 border-transparent hover:border-blue-200">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-blue-600 rounded-full mx-auto mb-6 flex items-center justify-center group-hover:from-blue-500 group-hover:to-blue-700 transition-all duration-300">
                <User className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-3">Sell (For Farmers)</h3>
              <p className="text-gray-600 mb-6">Choose this option if you are a farmer looking to sell products</p>
              <div className="inline-flex items-center text-blue-600 font-semibold group-hover:text-blue-700">
                Sell for Farmers
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </div>
            </div>
          </div>

          {/* Sell - Vendors */}
          <div 
            onClick={() => onSelectPerson('person2')}
            className="group cursor-pointer transform hover:scale-105 transition-all duration-300"
          >
            <div className="bg-white rounded-2xl shadow-lg hover:shadow-2xl p-8 text-center border-2 border-transparent hover:border-purple-200">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-400 to-purple-600 rounded-full mx-auto mb-6 flex items-center justify-center group-hover:from-purple-500 group-hover:to-purple-700 transition-all duration-300">
                <User className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-3">Sell (For Vendors)</h3>
              <p className="text-gray-600 mb-6">Choose this option if you are a vendor looking to sell products</p>
              <div className="inline-flex items-center text-purple-600 font-semibold group-hover:text-purple-700">
                Sell for Vendors
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </div>
            </div>
          </div>

          {/* Buy - Vendors */}
          <div 
            onClick={() => onSelectPerson('person3')}
            className="group cursor-pointer transform hover:scale-105 transition-all duration-300"
          >
            <div className="bg-white rounded-2xl shadow-lg hover:shadow-2xl p-8 text-center border-2 border-transparent hover:border-green-200">
              <div className="w-16 h-16 bg-gradient-to-r from-green-400 to-green-600 rounded-full mx-auto mb-6 flex items-center justify-center group-hover:from-green-500 group-hover:to-green-700 transition-all duration-300">
                <User className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-3">Buy (For Vendors)</h3>
              <p className="text-gray-600 mb-6">Choose this option if you are a vendor looking to buy products</p>
              <div className="inline-flex items-center text-green-600 font-semibold group-hover:text-green-700">
                Buy for Vendors
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </div>
            </div>
          </div>

          {/* Other */}
          <div 
            onClick={() => onSelectPerson('person4')}
            className="group cursor-pointer transform hover:scale-105 transition-all duration-300"
          >
            <div className="bg-white rounded-2xl shadow-lg hover:shadow-2xl p-8 text-center border-2 border-transparent hover:border-gray-200">
              <div className="w-16 h-16 bg-gradient-to-r from-gray-400 to-gray-600 rounded-full mx-auto mb-6 flex items-center justify-center group-hover:from-gray-500 group-hover:to-gray-700 transition-all duration-300">
                <User className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-800 mb-3">Other</h3>
              <p className="text-gray-600 mb-6">Choose this if none of the above match your role</p>
              <div className="inline-flex items-center text-gray-600 font-semibold group-hover:text-gray-700">
                Continue
                <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const DetailsPage = ({ personType, onSubmitDetails, onBack }) => {
  const [formData, setFormData] = useState({
    name: '', // ✅ Added name field
    cropType: '',
    quantity: '',
    qualityGrade: '',
    farmerLocation: '',
    spoilageDate: ''
  });

  const [errors, setErrors] = useState({});

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // ✅ Name validation
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.cropType.trim()) {
      newErrors.cropType = 'Crop type is required';
    }

    if (!formData.quantity.trim()) {
      newErrors.quantity = 'Quantity is required';
    } else if (isNaN(formData.quantity) || formData.quantity <= 0) {
      newErrors.quantity = 'Please enter a valid quantity';
    }

    if (!formData.qualityGrade.trim()) {
      newErrors.qualityGrade = 'Quality grade is required';
    }

    if (!formData.farmerLocation.trim()) {
      newErrors.farmerLocation = 'Pincode is required';
    } else if (!/^\d{6}$/.test(formData.farmerLocation)) {
      newErrors.farmerLocation = 'Please enter a valid 6-digit pincode';
    }

    if (!formData.spoilageDate.trim()) {
      newErrors.spoilageDate = 'Spoilage date is required';
    }

    return newErrors;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const newErrors = validateForm();

    if (Object.keys(newErrors).length === 0) {
      onSubmitDetails(formData);
    } else {
      setErrors(newErrors);
    }
  };

  const isPersonOne = personType === 'person1';
  const gradientColor = isPersonOne ? 'from-blue-500 to-blue-600' : 'from-purple-500 to-purple-600';
  const buttonColor = isPersonOne ? 'bg-blue-500 hover:bg-blue-600' : 'bg-purple-500 hover:bg-purple-600';

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className={`inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r ${gradientColor} rounded-full mb-4`}>
              <User className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-800 mb-2">
              {isPersonOne ? 'Farmer' : 'Vendor'} Details
            </h2>
            <p className="text-gray-600">Enter your crop details to continue</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">

            {/* ✅ Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Name *
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 rounded-lg border ${errors.name ? 'border-red-300' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                placeholder="Enter your name"
              />
              {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
            </div>

            {/* Crop Type */}
            <div>
              <label htmlFor="cropType" className="block text-sm font-medium text-gray-700 mb-2">
                Crop Type *
              </label>
              <input
                type="text"
                id="cropType"
                name="cropType"
                value={formData.cropType}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 rounded-lg border ${errors.cropType ? 'border-red-300' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                placeholder="e.g. Wheat, Rice, Tomatoes"
              />
              {errors.cropType && <p className="mt-1 text-sm text-red-600">{errors.cropType}</p>}
            </div>

            {/* Quantity */}
            <div>
              <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-2">
                Quantity (in kg) *
              </label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                value={formData.quantity}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 rounded-lg border ${errors.quantity ? 'border-red-300' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                placeholder="Enter quantity"
              />
              {errors.quantity && <p className="mt-1 text-sm text-red-600">{errors.quantity}</p>}
            </div>

            {/* Quality Grade */}
            <div>
              <label htmlFor="qualityGrade" className="block text-sm font-medium text-gray-700 mb-2">
                Quality Grade *
              </label>
              <select
                id="qualityGrade"
                name="qualityGrade"
                value={formData.qualityGrade}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 rounded-lg border ${errors.qualityGrade ? 'border-red-300' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
              >
                <option value="">Select grade</option>
                <option value="A">A - Premium</option>
                <option value="B">B - Good</option>
                <option value="C">C - Average</option>
                <option value="D">D - Below Average</option>
              </select>
              {errors.qualityGrade && <p className="mt-1 text-sm text-red-600">{errors.qualityGrade}</p>}
            </div>

            {/* Farmer Location (Pincode) */}
            <div>
              <label htmlFor="farmerLocation" className="block text-sm font-medium text-gray-700 mb-2">
                Farmer Pincode *
              </label>
              <input
                type="number"
                id="farmerLocation"
                name="farmerLocation"
                value={formData.farmerLocation}
                onChange={(e) => {
                  if (e.target.value.length <= 6) {
                    handleInputChange(e);
                  }
                }}
                className={`w-full px-4 py-3 rounded-lg border ${
                  errors.farmerLocation ? 'border-red-300' : 'border-gray-300'
                } focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
                placeholder="Enter 6-digit pincode"
              />
              {errors.farmerLocation && <p className="mt-1 text-sm text-red-600">{errors.farmerLocation}</p>}
            </div>

            {/* Spoilage Date */}
            <div>
              <label htmlFor="spoilageDate" className="block text-sm font-medium text-gray-700 mb-2">
                Expected Spoilage Date *
              </label>
              <input
                type="date"
                id="spoilageDate"
                name="spoilageDate"
                value={formData.spoilageDate}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 rounded-lg border ${errors.spoilageDate ? 'border-red-300' : 'border-gray-300'} focus:ring-2 focus:ring-blue-500 focus:border-blue-500`}
              />
              {errors.spoilageDate && <p className="mt-1 text-sm text-red-600">{errors.spoilageDate}</p>}
            </div>

            {/* Buttons */}
            <div className="flex space-x-4 pt-6">
              <button
                type="button"
                onClick={onBack}
                className="p-2 rounded-full bg-white shadow-md hover:bg-gray-100 transition flex items-center justify-center"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </button>
              <button
                type="submit"
                className={`flex-1 px-6 py-3 ${buttonColor} text-white rounded-lg font-medium flex items-center justify-center`}
              >
                Continue to Chat
                <ArrowRight className="w-4 h-4 ml-2" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};


// Chatbot Component (Updated to show user info)
const AIChatbot = ({ userDetails, onBack }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      content: `Hello ${userDetails.name}! Welcome to the AI Chatbot. I see you're interested in ${userDetails.preferences || 'general assistance'}. How can I help you today?`,
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  // Available AI models
  const availableModels = [
    { id: 'gpt-4', name: 'GPT-4', provider: 'OpenAI' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', provider: 'OpenAI' },
    { id: 'claude-3', name: 'Claude 3', provider: 'Anthropic' },
    { id: 'gemini-pro', name: 'Gemini Pro', provider: 'Google' },
  ];

  // AI API call function - PLACEHOLDER FOR YOUR BACKEND INTEGRATION
  // const callAIAPI = async (prompt, model) => {
  //   try {
  //     // TODO: Replace this with your actual AI/ML backend endpoint
  //     // Include user details in the API call for personalization
      
  //     // Example API call with user context:
  //     // const response = await fetch('/api/chat', {
  //     //   method: 'POST',
  //     //   headers: { 'Content-Type': 'application/json' },
  //     //   body: JSON.stringify({
  //     //     prompt: prompt,
  //     //     model: model,
  //     //     userContext: {
  //     //       name: userDetails.name,
  //     //       age: userDetails.age,
  //     //       preferences: userDetails.preferences,
  //     //       email: userDetails.email
  //     //     }
  //     //   })
  //     // });

  //     // MOCK RESPONSE - Replace with actual API call
  //     await new Promise(resolve => setTimeout(resolve, 1500));
      
  //     const mockResponses = [
  //       `Hi ${userDetails.name}! This is a response from ${model}. Based on your preference for ${userDetails.preferences || 'general assistance'}, I'm here to help!`,
  //       `Great question, ${userDetails.name}! As an AI using ${model}, I can assist you with that. Your message was: "${prompt.substring(0, 50)}${prompt.length > 50 ? '...' : ''}"`,
  //       `Hello ${userDetails.name}! I see you're ${userDetails.age} years old and interested in ${userDetails.preferences || 'various topics'}. Let me help you with: "${prompt}"`
  //     ];
      
  //     return {
  //       success: true,
  //       response: mockResponses[Math.floor(Math.random() * mockResponses.length)]
  //     };

  //   } catch (error) {
  //     return {
  //       success: false,
  //       error: error.message || 'Failed to get AI response'
  //     };
  //   }
  // };
  const sendAudioToAI = async (audioBlob, model) => {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('model', model);
    formData.append('userContext', JSON.stringify(userDetails));

    try {
      const response = await fetch('/api/audio-chat', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      // Backend should return transcription + AI reply
      return data;
    } catch (error) {
      return { success: false, error: error.message || 'Failed to send audio' };
    }
  };

  const callAIAPI = async (prompt, model) => {
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          model,
          userContext: {
            name: userDetails.name,
            cropType: userDetails.cropType,
            quantity: userDetails.quantity,
            qualityGrade: userDetails.qualityGrade,
            farmerLocation: userDetails.farmerLocation,
            spoilageDate: userDetails.spoilageDate
          }
        })
      });
      console.log(response);
      const data = await response.json();
      return data;

    } catch (error) {
      return { success: false, error: error.message || 'Failed to call AI API' };
    }
  };


  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Call AI API
    const aiResult = await callAIAPI(inputMessage, selectedModel);

    const botMessage = {
      id: Date.now() + 1,
      content: aiResult.success ? aiResult.response : `Error: ${aiResult.error}`,
      sender: 'bot',
      timestamp: new Date(),
      model: selectedModel,
      error: !aiResult.success
    };

    setMessages(prev => [...prev, botMessage]);
    setIsLoading(false);
  };

  // // 🎤 Start/Stop recording
  // const toggleRecording = async () => {
  //   if (isRecording) {
  //     mediaRecorderRef.current.stop();
  //     setIsRecording(false);
  //   } else {
  //     try {
  //       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  //       const mediaRecorder = new MediaRecorder(stream);
  //       mediaRecorderRef.current = mediaRecorder;
  //       audioChunksRef.current = [];

  //       mediaRecorder.ondataavailable = (e) => {
  //         if (e.data.size > 0) {
  //           audioChunksRef.current.push(e.data);
  //         }
  //       };

  //       mediaRecorder.onstop = async () => {
  //         const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
  //         const formData = new FormData();
  //         formData.append('audio', audioBlob);
  //         formData.append('model', selectedModel);
  //         formData.append('userContext', JSON.stringify(userDetails));

  //         // Send to backend for transcription (Gemini/OpenAI Whisper/etc.)
  //         try {
  //           const response = await fetch('/api/audio-chat', {
  //             method: 'POST',
  //             body: formData
  //           });
  //           const data = await response.json();

  //           if (data.success) {
  //             handleSendMessage(data.transcription);
  //           } else {
  //             setMessages(prev => [...prev, {
  //               id: Date.now(),
  //               content: `Error: ${data.error}`,
  //               sender: 'bot',
  //               error: true
  //             }]);
  //           }
  //         } catch (err) {
  //           console.error(err);
  //         }
  //       };

  //       mediaRecorder.start();
  //       setIsRecording(true);
  //     } catch (err) {
  //       alert('Microphone access denied or not available.');
  //     }
  //   }
  // };

  // 🎤 Start/Stop recording
const toggleRecording = async () => {
  if (isRecording) {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  } else {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", audioBlob);
        formData.append("model", selectedModel);
        formData.append("userContext", JSON.stringify(userDetails));

        try {
          setIsLoading(true);

          const response = await fetch("/api/audio-chat", {
            method: "POST",
            body: formData,
          });
          const data = await response.json();

          if (data.success) {
            // Add transcription as user message
            const userMessage = {
              id: Date.now(),
              content: data.transcription || "[🎤 Voice message]",
              sender: "user",
              timestamp: new Date(),
            };
            setMessages((prev) => [...prev, userMessage]);

            // Add AI response as bot message
            const botMessage = {
              id: Date.now() + 1,
              content: data.response,
              sender: "bot",
              timestamp: new Date(),
              model: selectedModel,
            };
            setMessages((prev) => [...prev, botMessage]);
          } else {
            setMessages((prev) => [
              ...prev,
              {
                id: Date.now(),
                content: `Error: ${data.error}`,
                sender: "bot",
                error: true,
              },
            ]);
          }

          setIsLoading(false);
        } catch (err) {
          console.error(err);
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              content: "Error: Failed to process audio",
              sender: "bot",
              error: true,
            },
          ]);
          setIsLoading(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert("Microphone access denied or not available.");
    }
  }
};


  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-lg border-b">
        <div className="w-full px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={onBack}
                className="p-2 rounded-full bg-white shadow-md hover:bg-gray-100 transition flex items-center justify-center"
              >
                <ArrowLeft className="w-5 h-5 text-gray-600" />
              </button>
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">AI Chatbot</h1>
                <p className="text-sm text-gray-600">
                  Welcome {userDetails.name} • Model: {selectedModel}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <select 
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                {availableModels.map(model => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.provider})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-hidden w-full">
        <div className="h-full flex flex-col w-full">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map(message => (
              <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl flex ${message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'} items-end space-x-2`}>
                  <div className={`p-2 rounded-full ${message.sender === 'user' ? 'bg-blue-500' : 'bg-gray-300'}`}>
                    {message.sender === 'user' ? 
                      <User className="w-4 h-4 text-white" /> : 
                      <Bot className="w-4 h-4 text-gray-600" />
                    }
                  </div>
                  <div className={`px-4 py-3 rounded-2xl ${
                    message.sender === 'user' 
                      ? 'bg-blue-500 text-white rounded-br-sm' 
                      : message.error 
                        ? 'bg-red-50 border border-red-200 text-red-800 rounded-bl-sm'
                        : 'bg-white shadow-sm border border-gray-200 text-gray-800 rounded-bl-sm'
                  }`}>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                    {message.sender === 'bot' && !message.error && (
                      <p className="text-xs mt-2 opacity-60">Model: {message.model}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-3xl flex items-end space-x-2">
                  <div className="p-2 rounded-full bg-gray-300">
                    <Bot className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="px-4 py-3 bg-white shadow-sm border border-gray-200 rounded-2xl rounded-bl-sm">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area
          <div className="border-t bg-white p-4">
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`Hi ${userDetails.name}, type your message here...`}
                className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 min-h-[50px] max-h-32"
                rows="1"
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className={`px-6 py-3 rounded-lg transition-colors ${
                  !inputMessage.trim() || isLoading
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div> */}
          {/* Input + Audio */}
          <div className="border-t bg-white p-4 flex space-x-2">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`Hi ${userDetails.name}, type or record your message...`}
              className="flex-1 resize-none border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500 min-h-[50px] max-h-32"
              rows="1"
              disabled={isLoading}
            />
            <button
              onClick={toggleRecording}
              className={`px-4 py-3 rounded-lg ${isRecording ? 'bg-red-500' : 'bg-gray-200'} text-white`}
            >
              {isRecording ? <Square className="w-5 h-5" /> : <Mic className="w-5 h-5 text-black" />}
            </button>
            <button
              onClick={() => handleSendMessage(inputMessage)}
              disabled={!inputMessage.trim() || isLoading}
              className={`px-6 py-3 rounded-lg transition-colors ${
                !inputMessage.trim() || isLoading
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [currentPage, setCurrentPage] = useState('welcome'); // 'welcome', 'details', 'chat'
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [userDetails, setUserDetails] = useState(null);

  const handlePersonSelect = (personType) => {
    setSelectedPerson(personType);
    setCurrentPage('details');
  };

  const handleDetailsSubmit = (details) => {
    setUserDetails({ ...details, personType: selectedPerson });
    setCurrentPage('chat');
  };

  const handleBackToWelcome = () => {
    setCurrentPage('welcome');
    setSelectedPerson(null);
    setUserDetails(null);
  };

  const handleBackToDetails = () => {
    setCurrentPage('details');
  };

  // Render current page
  if (currentPage === 'welcome') {
    return <WelcomePage onSelectPerson={handlePersonSelect} />;
  }

  if (currentPage === 'details') {
    return (
      <DetailsPage 
        personType={selectedPerson}
        onSubmitDetails={handleDetailsSubmit}
        onBack={handleBackToWelcome}
      />
    );
  }

  if (currentPage === 'chat') {
    return (
      <AIChatbot 
        userDetails={userDetails}
        onBack={handleBackToDetails}
      />
    );
  }

  return null;
};

export default App;