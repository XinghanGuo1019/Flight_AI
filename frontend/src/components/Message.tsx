// src/components/Message.tsx
import React, { useState, useEffect } from "react";
import ConfirmationModal from "./ConfirmationModal";
import "../styles/ChatBox.css";
import "../styles/ConfirmationModal.css";
import { FlightDetails } from "./ConfirmationModal";

interface MessageProps {
  sender: "user" | "assistant" | "system";
  text: string;
  flightUrl?: string;
  onSendMessage: (message: string) => void;
}

const Message: React.FC<MessageProps> = ({
  sender,
  text,
  flightUrl,
  onSendMessage,
}) => {
  const [showModal, setShowModal] = useState(false);
  const [flightDetails, setFlightDetails] = useState<FlightDetails | null>(
    null
  );
  const handleConfirm = () => {
    onSendMessage("Confirm Change");
    setShowModal(false);
  };
  const handleCancel = () => {
    onSendMessage("Re-search");
    setShowModal(false);
  };
  const extractFlightDetails = (text: string): FlightDetails | null => {
    try {
      // 机场信息解析
      const departureMatch = text.match(/Departure Airport: (.+?)\((\w+)\)/);
      const arrivalMatch = text.match(/Arrival Airport: (.+?)\((\w+)\)/);

      // 出发航班信息
      const departureDateMatch = text.match(
        /Departure Date: (\d{2}\/\d{2}\/\d{4})/
      );
      const departureTimeMatch = text.match(/Departure Time: (\d{2}:\d{2})/);
      const arrivalDateMatch = text.match(
        /Arrival Date: (\d{2}\/\d{2}\/\d{4})/
      );
      const arrivalTimeMatch = text.match(/Arrival Time: (\d{2}:\d{2})/);

      // 返程航班信息
      const returnDepartureDateMatch = text.match(
        /Return Date: (\d{2}\/\d{2}\/\d{4})/
      );
      const returnDepartureTimeMatch = text.match(
        /Return Departure Time: (\d{2}:\d{2})/
      );
      const returnArrivalDateMatch = text.match(
        /Return Arrival Date: (\d{2}\/\d{2}\/\d{4})/
      );
      const returnArrivalTimeMatch = text.match(
        /Return Arrival Time: (\d{2}:\d{2})/
      );

      // 价格信息
      const priceMatch = text.match(/Price USD: (\$\d+\.\d{2})/);
      const flightNumberMatch = text.match(/Flight Number: (\w+)/);

      if (!departureMatch || !arrivalMatch) return null;

      return {
        departureAirport: departureMatch[1].trim(),
        departureCode: departureMatch[2],
        arrivalAirport: arrivalMatch[1].trim(),
        arrivalCode: arrivalMatch[2],
        departureDate: departureDateMatch?.[1] || "",
        departureTime: departureTimeMatch?.[1] || "",
        arrivalDate: arrivalDateMatch?.[1] || "",
        arrivalTime: arrivalTimeMatch?.[1] || "",
        returnDepartureDate: returnDepartureDateMatch?.[1] || "",
        returnDepartureTime: returnDepartureTimeMatch?.[1] || "",
        returnArrivalDate: returnArrivalDateMatch?.[1] || "",
        returnArrivalTime: returnArrivalTimeMatch?.[1] || "",
        price: priceMatch?.[1] || "$0.00",
        flightNumber: flightNumberMatch?.[1] || "",
      };
    } catch (error) {
      console.error("Error parsing flight details:", error);
      return null;
    }
  };
  useEffect(() => {
    if (text.toLowerCase().includes("alternative ticket")) {
      const details = extractFlightDetails(text);
      if (details) {
        setFlightDetails(details);
        setShowModal(true);
      }
    }
  }, [text]);

  return (
    <div className={`message ${sender}`}>
      <div className="message-content">
        <div dangerouslySetInnerHTML={{ __html: text }} />
        {flightUrl && (
          <a href={flightUrl} target="_blank" rel="noopener noreferrer">
            See flight details
          </a>
        )}
      </div>

      {showModal && flightDetails && (
        <ConfirmationModal
          flightDetails={flightDetails}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}
    </div>
  );
};

export default Message;
