import { describe, it, expect } from 'vitest';
import { compactNumber } from './format';

describe("compactNumber", () => {
    it("formats large numbers", () => {
        expect(compactNumber(123456)).toBe("123,456");
    });

    it("formats small numbers", () => {
        expect(compactNumber(123)).toBe("123");
    });

    it("returns '--' for null", () => {
        expect(compactNumber(null)).toBe("--");
    });

    it("returns '--' for undefined", () => {
        expect(compactNumber(undefined)).toBe("--");
    });

    it("returns '--' for NaN", () => {
        expect(compactNumber(NaN)).toBe("--");
    });

    it("formats string numbers", () => {
        expect(compactNumber("123456")).toBe("123,456");
    });
});