// app/api/auth/[...nextauth]/route.ts
// AUTH DISABLED — route kept only to satisfy Next.js routing structure.

import { NextResponse } from "next/server";

export function GET() {
    return NextResponse.json({
        auth: false,
        message: "Authentication has been disabled.",
    });
}

export function POST() {
    return NextResponse.json({
        auth: false,
        message: "Authentication has been disabled.",
    });
}
