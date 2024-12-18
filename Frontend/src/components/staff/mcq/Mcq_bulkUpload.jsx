import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import GroupImage from "../../../assets/bulk.png";

const Mcq_bulkUpload  = () => {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestions, setSelectedQuestions] = useState([]);
  const [activeTab, setActiveTab] = useState("My Device"); // Default tab
  const [highlightStep, setHighlightStep] = useState(1); // Step highlight state
  const navigate = useNavigate();

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === "My Drive") setHighlightStep(1);
    else if (tab === "Dropbox") setHighlightStep(2);
    else if (tab === "My Device") setHighlightStep(3);
  };

  // Handle CSV Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) {
      alert("Please select a valid CSV file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = localStorage.getItem("contestToken");
      const response = await axios.post("http://localhost:8000/api/mcq/bulk-upload/", formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      setQuestions(response.data.questions);
      alert("File uploaded successfully! Preview the questions below.");
    } catch (error) {
      console.error("Error uploading file:", error);
      alert("Failed to upload the file. Please try again.");
    }
  };

  // Handle Question Selection
  const handleSelectQuestion = (index) => {
    setSelectedQuestions((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  // Submit Selected Questions
  const handleSubmit = async () => {
    const token = localStorage.getItem("contestToken");
    const selected = selectedQuestions.map((index) => questions[index]);

    try {
      await axios.post(
        "http://localhost:8000/api/mcq/save-questions/",
        { questions: selected },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      alert("Questions added successfully!");

      setQuestions([]);
      setSelectedQuestions([]);
      navigate('/mcq/QuestionsDashboard');
    } catch (error) {
      console.error("Error submitting questions:", error);
      alert("Failed to submit questions. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center">
      {/* Title Section */}
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Upload Files</h1>
        <p className="text-gray-500 text-sm">
          Easily add questions by uploading your prepared files as{" "}
          <span className="font-medium text-gray-600">csv, xlsx etc.</span>
        </p>
      </div>

      {/* Main Upload Section */}
      <div className="bg-white shadow-lg rounded-3xl p-8 w-[90%] max-w-4xl">

     
        {/* Tabs Section */}
        <div className="flex space-x-6 mb-6 justify-center">
          <button
            className={`font-medium ${
              activeTab === "My Drive"
                ? "border-b-2 border-black text-black"
                : "text-gray-500"
            }`}
            onClick={() => handleTabChange("My Drive")}
          >
            My Drive
          </button>
          <button
            className={`font-medium ${
              activeTab === "Dropbox"
                ? "border-b-2 border-black text-black"
                : "text-gray-500"
            }`}
            onClick={() => handleTabChange("Dropbox")}
          >
            Dropbox
          </button>
          <button
            className={`font-medium ${
              activeTab === "My Device"
                ? "border-b-2 border-black text-black"
                : "text-gray-500"
            }`}
            onClick={() => handleTabChange("My Device")}
          >
            My Device
          </button>
        </div>

        {/* Upload Section */}
        <div className="flex flex-col items-center justify-center mb-6">
          <img
            src={GroupImage}
            alt="Upload Illustration"
            className="w-48 h-48 object-contain mb-4"
          />
          <label
            htmlFor="fileInput"
            className="bg-yellow-400 text-black px-6 py-3 rounded-full shadow hover:bg-yellow-500 cursor-pointer transition"
          >
            Upload CSV
          </label>
          <input
            type="file"
            id="fileInput"
            style={{ display: "none" }}
            accept=".csv"
            onChange={handleFileUpload}
          />
        </div>
      </div>

      {/* Questions Preview Section */}
      {questions.length > 0 && (
        <div className="bg-white shadow-lg rounded-3xl p-6 mt-8 w-[90%] max-w-5xl">
          <h2 className="text-2xl font-semibold mb-4">Questions Preview</h2>
          <table className="table-auto w-full bg-white shadow-lg rounded-lg overflow-hidden">
            <thead className="bg-gray-200 text-gray-800">
              <tr>
                <th className="px-4 py-2">Select</th>
                <th className="px-4 py-2">Question</th>
                <th className="px-4 py-2">Options</th>
                <th className="px-4 py-2">Correct Answer</th>
                <th className="px-4 py-2">Mark</th>
                <th className="px-4 py-2">Negative Mark</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((q, index) => (
                <tr
                  key={index}
                  className={`${
                    index % 2 === 0 ? "bg-gray-100" : "bg-white"
                  } text-gray-800`}
                >
                  <td className="px-4 py-2 text-center">
                    <input
                      type="checkbox"
                      checked={selectedQuestions.includes(index)}
                      onChange={() => handleSelectQuestion(index)}
                    />
                  </td>
                  <td className="px-4 py-2">{q.question}</td>
                  <td className="px-4 py-2">{q.options.filter((opt) => opt).join(", ")}</td>
                  <td className="px-4 py-2">{q.correctAnswer}</td>
                  <td className="px-4 py-2 text-center">{q.mark}</td>
                  <td className="px-4 py-2 text-center">{q.negativeMark}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Submit Button */}
          <div className="flex justify-end mt-6">
            <button
              onClick={handleSubmit}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Submit Selected Questions
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Mcq_bulkUpload;
