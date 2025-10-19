<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('cubes', function (Blueprint $table) {
            $table->id();
            $table->foreignId('group_id')->constrained('group_of_three')->onDelete('cascade');
            $table->string('color');
            $table->string('face');
            $table->float('individual_time');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('cubes');
    }
};
