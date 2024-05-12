# Threaded PythonSV operator

## TODO

- [ ] aa

## Goals

- Optimize test flow
- Handle equipment failure independently of script advancement

## Ideas

Make the program live/ online. Meaning' that it always runs and gets queries from the user

## Flow

- Board ON
- Boot Script
- Load namenodes sv
- run test
  - init Data_Logger
  - connect to scope
  - connect to switch
  - connect to JBERT
  - run BringUp
  - load scope setup
  - load switch setup
  - load JBERT setp
  - configure PHY
  - save waveform(s)

## Dependency Tree

## Threads

1. Scope
2. JBERT
3. sv namespace
4. Test execution+
5. Core dump
6. Data aggregator (collect separate csv files)
7. error handler (send email or something)
