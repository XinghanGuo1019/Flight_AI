// src/components/ConfirmationModal.tsx
import React from "react";
import "../styles/ConfirmationModal.css";

export interface FlightDetails {
  departureAirport: string;
  flightNumber: string;
  departureCode: string;
  arrivalAirport: string;
  arrivalCode: string;
  departureDate: string;
  departureTime: string;
  arrivalDate: string;
  arrivalTime: string;
  returnDepartureDate: string;
  returnDepartureTime: string;
  returnArrivalDate: string;
  returnArrivalTime: string;
  price: string;
}

interface ConfirmationModalProps {
  flightDetails: FlightDetails;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  flightDetails,
  onConfirm,
  onCancel,
}) => {
  return (
    <div className="modal-overlay">
      <div className="modal-container">
        <div className="route-container">
          <div className="airport-group">
            <div className="airport-code">{flightDetails.departureCode}</div>
            <div className="airport-name">{flightDetails.departureAirport}</div>
          </div>
          <div className="flight-arrow">→</div>
          <div className="airport-group">
            <div className="airport-code">{flightDetails.arrivalCode}</div>
            <div className="airport-name">{flightDetails.arrivalAirport}</div>
          </div>
        </div>

        <div className="flight-details">
          <div className="detail-row">
            <div className="detail-item">
              <label>Departure</label>
              <div>{flightDetails.departureDate}</div>
              <div className="time">{flightDetails.departureTime}</div>
            </div>
            <div className="detail-item">
              <label>Arrival</label>
              <div>{flightDetails.arrivalDate}</div>
              <div className="time">{flightDetails.arrivalTime}</div>
            </div>
          </div>

          <div className="detail-row">
            <div className="detail-item">
              <label>Return Departure</label>
              <div>{flightDetails.returnDepartureDate}</div>
              <div className="time">{flightDetails.returnDepartureTime}</div>
            </div>
            <div className="detail-item">
              <label>Return Arrival</label>
              <div>{flightDetails.returnArrivalDate}</div>
              <div className="time">{flightDetails.returnArrivalTime}</div>
            </div>
          </div>

          <div className="price-section">
            <div className="price-label">Total Price</div>
            <div className="price-value">{flightDetails.price}</div>
          </div>
        </div>

        <div className="button-group">
          <button className="cancel-btn" onClick={onCancel}>
            Cancel
          </button>
          <button className="confirm-btn" onClick={onConfirm}>
            Confirm Change
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;
