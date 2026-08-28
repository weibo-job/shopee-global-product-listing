import AppKit
import Foundation
import Vision

struct OCRResult: Codable {
    let text: String?
    let error: String?
}

func recognizeText(at path: String) -> OCRResult {
    guard let image = NSImage(contentsOfFile: path) else {
        return OCRResult(text: nil, error: "cannot load image")
    }
    var proposed = CGRect(origin: .zero, size: image.size)
    guard let cgImage = image.cgImage(forProposedRect: &proposed, context: nil, hints: nil) else {
        return OCRResult(text: nil, error: "cannot decode image")
    }

    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true
    do {
        try VNImageRequestHandler(cgImage: cgImage, options: [:]).perform([request])
        let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
        return OCRResult(text: lines.joined(separator: "\n"), error: nil)
    } catch {
        let nsError = error as NSError
        return OCRResult(
            text: nil,
            error: "\(nsError.domain) code=\(nsError.code) \(nsError.localizedDescription) \(nsError.userInfo)"
        )
    }
}

var output: [String: OCRResult] = [:]
for argument in CommandLine.arguments.dropFirst() {
    output[argument] = recognizeText(at: argument)
}

do {
    let data = try JSONEncoder().encode(output)
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write(Data("\n".utf8))
} catch {
    FileHandle.standardError.write(Data("cannot encode OCR output: \(error)\n".utf8))
    exit(2)
}
