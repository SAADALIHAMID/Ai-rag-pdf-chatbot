import pymupdf as fitz
import os
from pathlib import Path

def create_sample_technical_pdf(output_path: str):
    doc = fitz.open()
    
    # Define color palette & styling
    primary_color = (0.05, 0.1, 0.25)
    accent_color = (0.1, 0.4, 0.8)
    text_color = (0.15, 0.15, 0.15)
    light_bg = (0.95, 0.97, 1.0)
    
    pages_content = [
        {
            "chapter": "CHAPTER 1: EXECUTIVE OVERVIEW & ARCHITECTURE",
            "page_title": "Project Quantum Aegis: System Specifications",
            "sections": [
                (
                    "1.1 Executive Summary",
                    "Project Quantum Aegis (Codename: Aegis-9) was initiated on October 14, 2026, under the direct supervision of Chief Architect Dr. Aris Thorne and Senior Systems Engineer Sarah Jenkins. The system is designed to provide autonomous fault-tolerant quantum computing clusters for aerospace trajectory optimization and real-time orbital calculations.\n\nThe initial production phase is deployed at the Atacama High-Altitude Observatory in Chile at an elevation of 5,050 meters above sea level."
                ),
                (
                    "1.2 High-Level Architecture Metrics",
                    "• Core Processing Matrix: 1,024 Superconducting Transmon Qubits.\n• Coherence Time (T2): Average 185 microseconds across all lattice gates.\n• Interconnect Bus: Photonic Quantum Waveguide with 99.98% single-qubit gate fidelity.\n• Dual-Phase Redundancy: Primary computing cluster backed by hot-standby node 'Borealis-2'.\n• Total Infrastructure Footprint: 450 square meters with Class 10 cleanroom certification."
                )
            ]
        },
        {
            "chapter": "CHAPTER 2: CRYOGENICS & HARDWARE SUBSYSTEMS",
            "page_title": "Dilution Refrigeration & Thermal Dissipation",
            "sections": [
                (
                    "2.1 Operating Temperatures and Coolants",
                    "The quantum processing core is housed inside a custom BlueFors XLD dilution refrigerator operating at a base temperature of 14.8 millikelvin. The system utilizes a closed-cycle Helium-3 / Helium-4 isotope mixture with an active circulation flow rate of 4.85 liters per minute.\n\nThe primary thermal dissipation radiator maintains an external jacket temperature of 4.2 Kelvin using liquid helium buffers."
                ),
                (
                    "2.2 Emergency Venting Protocols",
                    "In the event of vacuum breach or cryogenic overheating exceeding 85 millikelvin, automated burst disc 'BD-703' releases pressurized helium vapor into external holding tanks.\n\nThe emergency pressure relief threshold is strictly calibrated to 142.6 PSI (983.2 kPa). All emergency relief valves trigger within 18 milliseconds of sensor confirmation."
                )
            ]
        },
        {
            "chapter": "CHAPTER 3: SECURITY PROTOCOLS & CLEARANCE TIERS",
            "page_title": "Access Control, Biometrics & Master Override",
            "sections": [
                (
                    "3.1 Clearance Level Hierarchy",
                    "Access to the facility is categorized into four strict clearance tiers:\n• Level 1 (Observatory Staff): General observation decks and environmental telemetry.\n• Level 2 (Diagnostic Engineers): Access to secondary diagnostic bus and telemetry logs.\n• Level 3 (Quantum Physicists): Core calibration and pulse sequence programming.\n• Level 4 (Directorate Clearance): Cryogenic chamber physical hatch and firmware flash."
                ),
                (
                    "3.2 Master Hardware Security Key",
                    "Manual physical override of the core chamber requires simultaneous rotation of two physical keys separated by 3.5 meters. The master cryptographic key identifier for the digital firmware bypass is 'AEGIS-SEC-9942-OMEGA'.\n\nAttempting three unauthorized biometric fingerprint scans activates an automated facility lockdown within 250 milliseconds and alerts Chilean Federal Aerospace Security."
                )
            ]
        },
        {
            "chapter": "CHAPTER 4: POWER SUBSYSTEMS & CONTINUITY RESERVES",
            "page_title": "Electrical Distribution and Island Grid Operation",
            "sections": [
                (
                    "4.1 Primary Grid & Power Demand",
                    "Project Quantum Aegis consumes an uninterrupted steady-state electrical power of 185.4 Kilowatts. Power is fed from the Atacama Solar Thermal Array with an average collector efficiency rating of 38.4%.\n\nA dedicated 500 kVA harmonic filtration transformer ensures input voltage variation remains under 0.05% THD (Total Harmonic Distortion)."
                ),
                (
                    "4.2 Battery Backup and Autonomous Island Mode",
                    "For uninterrupted resilience during mountain storms, the facility houses a triple-redundant Lithium-Graphene solid-state energy storage module with a capacity of 1.2 Megawatt-hours (MWh).\n\nIn the event of total municipal grid disconnect, the system enters autonomous Island Mode and can sustain full cryogenic and computing operations for exactly 72 continuous hours without human intervention."
                )
            ]
        },
        {
            "chapter": "CHAPTER 5: INCIDENT HISTORY & CORRECTIVE ACTIONS",
            "page_title": "Log of Historical Anomalies and Rectifications",
            "sections": [
                (
                    "5.1 Incident Report IR-2025-0512",
                    "Date: May 12, 2025 (Pre-Commissioning Test Phase)\nLocation: Cryostat Expansion Bay 4, Sector 7.\nDescription: A micro-fracture in the secondary copper thermal anchor caused an unexpected thermal surge, raising base temperature to 320 millikelvin for 43 seconds.\n\nRoot Cause: Excessive torque applied to bolt M8-A during cold-head installation.\nCorrective Action: All cryogenic bolts replaced with Inconel-718 aerospace alloy tightened to a calibrated torque of 14.5 Newton-meters. No quantum processor damage occurred."
                ),
                (
                    "5.2 Protocol 404-Omega (Total Isolation)",
                    "Protocol 404-Omega is reserved exclusively for uncontained seismic events or hostile physical intrusion. Under this protocol, optical data links are severed mechanically via pyrotechnic cable cutters, and quantum state registers are zeroized with microwave depolarizing pulses within 4 milliseconds."
                )
            ]
        },
        {
            "chapter": "CHAPTER 6: BUDGET, CONTRACTORS & VENDORS",
            "page_title": "Financial Audit and Supply Chain Verification",
            "sections": [
                (
                    "6.1 Capital Expenditure & Budget",
                    "The total research, development, and deployment expenditure for Project Quantum Aegis across FY2024–FY2026 is $48,520,000 USD (Forty-Eight Million Five Hundred Twenty Thousand Dollars).\n\nFund breakdown:\n• 42% ($20.37M) - Quantum Processing Hardware & Superconducting Qubits.\n• 28% ($13.58M) - Dilution Refrigeration & Cryogenic Infrastructure.\n• 18% ($8.73M) - Cleanroom Facility Construction & Power Resilience.\n• 12% ($5.84M) - Software Orchestration, Hybrid Retrieval & AI Systems."
                ),
                (
                    "6.2 Primary Vendors & Contract Identifiers",
                    "• Cryogenic Systems: Helios Cryogenics Ltd. (Contract: CNT-2026-8819-HE)\n• Optical Resonators: Lumina Quantum Optics Corp. (Contract: CNT-2025-4102-LU)\n• Vacuum Seals & Flanges: ValvoMax Engineering (Contract: CNT-2026-1193-VM)\n• Annual Maintenance Audit Contact: compliance@aegis-quantum.org"
                )
            ]
        }
    ]

    for p_idx, p_data in enumerate(pages_content):
        page = doc.new_page(width=595, height=842) # Standard A4 page
        
        # Header banner
        page.draw_rect(fitz.Rect(36, 30, 559, 70), color=None, fill=primary_color)
        page.insert_text(fitz.Point(48, 48), p_data["chapter"], fontsize=9, color=(0.8, 0.9, 1.0), fontname="helv")
        page.insert_text(fitz.Point(48, 64), p_data["page_title"], fontsize=12, color=(1.0, 1.0, 1.0), fontname="helv")
        
        y = 100
        for sec_title, sec_body in p_data["sections"]:
            # Section Title
            page.draw_rect(fitz.Rect(36, y, 40, y + 16), color=None, fill=accent_color)
            page.insert_text(fitz.Point(48, y + 13), sec_title, fontsize=11, color=primary_color, fontname="helv")
            y += 26
            
            # Section Text Box
            rect = fitz.Rect(36, y, 559, y + 250)
            rc = page.insert_textbox(rect, sec_body, fontsize=9.5, color=text_color, fontname="helv", lineheight=1.4)
            y += 180

        # Footer
        page.draw_line(fitz.Point(36, 800), fitz.Point(559, 800), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text(fitz.Point(36, 815), "CONFIDENTIAL // PROJECT QUANTUM AEGIS TECHNICAL SPECIFICATION // RESTRICTED", fontsize=7.5, color=(0.5, 0.5, 0.5), fontname="helv")
        page.insert_text(fitz.Point(530, 815), f"Page {p_idx + 1} of {len(pages_content)}", fontsize=8, color=(0.3, 0.3, 0.3), fontname="helv")

    doc.save(output_path)
    doc.close()
    print(f"Successfully created PDF: {output_path}")

if __name__ == "__main__":
    out_dir = Path(r"d:\ai projects\chatbot\test_documents")
    out_dir.mkdir(parents=True, exist_ok=True)
    target_file = out_dir / "Project_Quantum_Aegis_Technical_Manual.pdf"
    create_sample_technical_pdf(str(target_file))
