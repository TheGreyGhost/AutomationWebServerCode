-- phpMyAdmin SQL Dump
-- version 4.6.6deb4
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Feb 03, 2019 at 04:54 PM
-- Server version: 10.1.23-MariaDB-9+deb9u1
-- PHP Version: 7.0.27-0+deb9u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `AutomationServerRealtime`
--

-- --------------------------------------------------------

--
-- Table structure for table `PoolHeaterSensorValues`
--

CREATE TABLE `PoolHeaterSensorValues` (
  `entry_number` int(11) NOT NULL,
  `timestamp` int(11) NOT NULL,
  `sim_flags` bit(16) NOT NULL,
  `solar_intensity` float NOT NULL,
  `cumulative_insolation` float NOT NULL,
  `surge_tank_ok` tinyint(1) NOT NULL,
  `pump_runtime` float NOT NULL,
  `hx_hot_inlet_inst` float NOT NULL,
  `hx_hot_inlet_smooth` float NOT NULL,
  `hx_hot_outlet_inst` float NOT NULL,
  `hx_hot_outlet_smooth` float NOT NULL,
  `hx_cold_inlet_inst` float NOT NULL,
  `hx_cold_inlet_smooth` float NOT NULL,
  `hx_cold_outlet_inst` float NOT NULL,
  `hx_cold_outlet_smooth` float NOT NULL,
  `temp_ambient_inst` float NOT NULL,
  `temp_ambient_smooth` float NOT NULL
) ENGINE=MEMORY DEFAULT CHARSET=utf8mb4 COMMENT='Temporary storage of the current sensor values';

--
-- Indexes for dumped tables
--

--
-- Indexes for table `PoolHeaterSensorValues`
--
ALTER TABLE `PoolHeaterSensorValues`
  ADD PRIMARY KEY (`entry_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `PoolHeaterSensorValues`
--
ALTER TABLE `PoolHeaterSensorValues`
  MODIFY `entry_number` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
