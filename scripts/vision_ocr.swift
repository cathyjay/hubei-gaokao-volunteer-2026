#!/usr/bin/env swift
import Foundation
import ImageIO
import Vision

struct BoundingBox: Codable {
    let x: Double
    let y: Double
    let width: Double
    let height: Double
}

struct OCRLine: Codable {
    let text: String
    let confidence: Float
    let boundingBox: BoundingBox
}

struct OCRResult: Codable {
    let image: String
    let engine: String
    let languages: [String]
    let lineCount: Int
    let averageConfidence: Float?
    let text: String
    let lines: [OCRLine]
    let error: String?
}

func usage() -> Never {
    fputs("""
    Usage: vision_ocr.swift [--languages zh-Hans,en-US] [--fast] IMAGE...

    Outputs one JSON object per input image, one per line.
    """, stderr)
    exit(2)
}

var args = Array(CommandLine.arguments.dropFirst())
var languages = ["zh-Hans", "en-US"]
var recognitionLevel = VNRequestTextRecognitionLevel.accurate
var images: [String] = []

while let arg = args.first {
    args.removeFirst()
    switch arg {
    case "--languages":
        guard let value = args.first else { usage() }
        args.removeFirst()
        languages = value
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
    case "--fast":
        recognitionLevel = .fast
    case "--help", "-h":
        usage()
    default:
        images.append(arg)
    }
}

if images.isEmpty {
    usage()
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]

func imageOrientation(from source: CGImageSource) -> CGImagePropertyOrientation {
    guard
        let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
        let raw = properties[kCGImagePropertyOrientation] as? UInt32,
        let orientation = CGImagePropertyOrientation(rawValue: raw)
    else {
        return .up
    }
    return orientation
}

func emit(_ result: OCRResult) {
    do {
        let data = try encoder.encode(result)
        if let line = String(data: data, encoding: .utf8) {
            print(line)
        }
    } catch {
        fputs("Failed to encode OCR result: \(error)\n", stderr)
    }
}

for imagePath in images {
    let url = URL(fileURLWithPath: imagePath)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let cgImage = CGImageSourceCreateImageAtIndex(source, 0, nil)
    else {
        emit(OCRResult(
            image: imagePath,
            engine: "apple_vision",
            languages: languages,
            lineCount: 0,
            averageConfidence: nil,
            text: "",
            lines: [],
            error: "Cannot load image"
        ))
        continue
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = recognitionLevel
    request.usesLanguageCorrection = true
    request.recognitionLanguages = languages

    let handler = VNImageRequestHandler(
        cgImage: cgImage,
        orientation: imageOrientation(from: source),
        options: [:]
    )

    do {
        try handler.perform([request])
        let observations = request.results ?? []
        let lines = observations.compactMap { observation -> OCRLine? in
            guard let candidate = observation.topCandidates(1).first else {
                return nil
            }
            let box = observation.boundingBox
            return OCRLine(
                text: candidate.string,
                confidence: candidate.confidence,
                boundingBox: BoundingBox(
                    x: Double(box.origin.x),
                    y: Double(box.origin.y),
                    width: Double(box.size.width),
                    height: Double(box.size.height)
                )
            )
        }
        let text = lines.map(\.text).joined(separator: "\n")
        let averageConfidence = lines.isEmpty
            ? nil
            : lines.map(\.confidence).reduce(0, +) / Float(lines.count)

        emit(OCRResult(
            image: imagePath,
            engine: "apple_vision",
            languages: languages,
            lineCount: lines.count,
            averageConfidence: averageConfidence,
            text: text,
            lines: lines,
            error: nil
        ))
    } catch {
        emit(OCRResult(
            image: imagePath,
            engine: "apple_vision",
            languages: languages,
            lineCount: 0,
            averageConfidence: nil,
            text: "",
            lines: [],
            error: String(describing: error)
        ))
    }
}
