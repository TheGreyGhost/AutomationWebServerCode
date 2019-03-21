-- phpMyAdmin SQL Dump
-- version 4.6.6deb4
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Mar 21, 2019 at 11:42 PM
-- Server version: 10.1.23-MariaDB-9+deb9u1
-- PHP Version: 7.0.27-0+deb9u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `AutomationServerHistory`
--

-- --------------------------------------------------------

--
-- Table structure for table `LoggedData`
--

CREATE TABLE `LoggedData` (
  `datastore_hash` int(10) UNSIGNED NOT NULL,
  `row_number` int(10) UNSIGNED NOT NULL,
  `timestampUTC` int(10) UNSIGNED NOT NULL,
  `hx_hot_inlet_min` float NOT NULL,
  `hx_hot_inlet_ave` float NOT NULL,
  `hx_hot_inlet_max` float NOT NULL,
  `hx_hot_outlet_min` float NOT NULL,
  `hx_hot_outlet_ave` float NOT NULL,
  `hx_hot_outlet_max` float NOT NULL,
  `hx_cold_inlet_min` float NOT NULL,
  `hx_cold_inlet_ave` float NOT NULL,
  `hx_cold_inlet_max` float NOT NULL,
  `hx_cold_outlet_min` float NOT NULL,
  `hx_cold_outlet_ave` float NOT NULL,
  `hx_cold_outlet_max` float NOT NULL,
  `temp_ambient_min` float NOT NULL,
  `temp_ambient_ave` float NOT NULL,
  `temp_ambient_max` float NOT NULL,
  `cumulative_insolation` float NOT NULL,
  `surgetank_level` float NOT NULL,
  `pump_runtime` float NOT NULL,
  `pump_state` smallint(5) UNSIGNED NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `TimeStampCorrection`
--

CREATE TABLE `TimeStampCorrection` (
  `entry_number` int(11) NOT NULL,
  `arduino_timestamp` int(11) NOT NULL,
  `rpi_timestamp` int(11) NOT NULL,
  `arduino_seconds_ahead` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `LoggedData`
--
ALTER TABLE `LoggedData`
  ADD PRIMARY KEY (`datastore_hash`,`row_number`);

--
-- Indexes for table `TimeStampCorrection`
--
ALTER TABLE `TimeStampCorrection`
  ADD PRIMARY KEY (`entry_number`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `TimeStampCorrection`
--
ALTER TABLE `TimeStampCorrection`
  MODIFY `entry_number` int(11) NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
