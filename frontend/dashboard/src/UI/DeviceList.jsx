import DeviceCard from "./DeviceCard";
import { devices } from "../constants";

const DeviceList = () => {
  return (
    <div className="flex flex-wrap gap-6 justify-center p-5">
      {devices.map((device, index) => (
        <DeviceCard key={index} device={device} />
      ))}
    </div>
  );
};

export default DeviceList;
